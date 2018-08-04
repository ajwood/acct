import pandas as pd
import numpy as np
import sqlite3
import argparse
import datetime
import logging

DISPLAY_WIDTH = 98
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

class Accounts(object):
	def __init__(self, conn=None):
		if conn is None:
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/acct.db')
				website = True
			except:
				conn = sqlite3.connect('acct.db')
		elif isinstance(conn, str):
			conn = sqlite3.connect(conn)
		else:
			conn = sqlite3.connect('acct.db')

		Accounts.conn = conn

		try:
			self.refresh_accts()
		except:
			Accounts.df = None
			self.create_accts()
			self.refresh_accts()

	def create_accts(self):
		create_accts_query = '''
			CREATE TABLE IF NOT EXISTS accounts (
				accounts text,
				child_of text
			);
			'''
		standard_accts = [
			['Account','None'],
			['Admin','Account'],
			['Asset','Account'],
			['Equity','Account'],
			['Liability','Equity'],
			['Wealth','Equity'],
			['Revenue','Wealth'],
			['Expense','Wealth'],
			['Transfer','Wealth']]

		cur = self.conn.cursor()
		cur.execute(create_accts_query)
		for acct in standard_accts:
				account = str(acct[0])
				child_of = str(acct[1])
				print(acct)
				details = (account,child_of)
				cur.execute('INSERT INTO accounts VALUES (?,?)', details)
		self.conn.commit()
		cur.close()

	def refresh_accts(self):
		Accounts.df = pd.read_sql_query('SELECT * FROM accounts;', self.conn, index_col='accounts')

	def print_accts(self):
		self.refresh_accts()
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print (Accounts.df)
		print ('-' * DISPLAY_WIDTH)
		return Accounts.df

	def drop_dupe_accts(self):
		Accounts.df = Accounts.df[~Accounts.df.index.duplicated(keep='first')]
		Accounts.df.to_sql('accounts', self.conn, if_exists='replace')
		self.refresh_accts()

	def add_acct(self, acct_data = None):
		cur = self.conn.cursor()
		if acct_data is None:
			account = input('Enter the account name: ')
			child_of = input('Enter the parent account: ')
			if child_of not in Accounts.df.index:
				print ('\n' + child_of + ' is not a valid account.')
				return

			details = (account,child_of)
			cur.execute('INSERT INTO accounts VALUES (?,?)', details)
			
		else:
			for acct in acct_data:
				account = str(acct[0])
				child_of = str(acct[1])
				print(acct)

				details = (account,child_of)
				cur.execute('INSERT INTO accounts VALUES (?,?)', details)

		self.conn.commit()
		cur.close()
		self.refresh_accts()
		self.drop_dupe_accts()

		# TODO Add error checking to ensure all accounts lead to a standard account

	def load_accts(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			load_df = pd.read_csv(f, keep_default_na=False)
			lol = load_df.values.tolist()
			print (load_df)
			print ('-' * DISPLAY_WIDTH)
			self.add_acct(lol)

	def export_accts(self):
		outfile = 'accounts_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		Accounts.df.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
		print ('File saved as ' + save_location + outfile + '\n')

	def remove_acct(self):
		acct = input('Which account would you like to remove? ')
		cur = self.conn.cursor()
		cur.execute('DELETE FROM accounts WHERE accounts=?', (acct,))
		self.conn.commit()
		cur.close()
		self.refresh_accts()

class Ledger(Accounts):
	def __init__(self, ledger_name=None, entity=None, date=None, start_date=None, txn=None):
		self.conn = Accounts.conn
		if ledger_name is None:
			self.ledger_name = 'random_1' #input('Enter a name for the ledger: ')
		else:
			self.ledger_name = ledger_name
		self.entity = entity
		self.date = date
		self.start_date = start_date
		self.txn = txn
		self.create_ledger()
		self.refresh_ledger()
		self.balance_sheet()
			
	def create_ledger(self): # TODO Change entity_id to string type
		create_ledger_query = '''
			CREATE TABLE IF NOT EXISTS ledger_''' + self.ledger_name + ''' (
				txn_id INTEGER PRIMARY KEY,
				event_id integer NOT NULL,
				entity_id integer NOT NULL,
				date date NOT NULL,
				description text,
				item_id text,
				price real,
				qty integer,
				debit_acct text,
				credit_acct text,
				amount real NOT NULL
			);
			'''

		cur = self.conn.cursor()
		cur.execute(create_ledger_query)
		self.conn.commit()
		cur.close()

	def set_entity(self, entity=None):
		self.entity = int(input('Enter an Entity ID: ')) # TODO Change entity_id to string type
		self.refresh_ledger()
		self.balance_sheet()
		return self.entity

	def set_date(self, date=None):
		self.date = input('Enter a date in format YYYY-MM-DD: ')
		self.refresh_ledger()
		self.balance_sheet()
		return self.date

	def set_start_date(self, date=None):
		self.start_date = input('Enter a date in format YYYY-MM-DD: ')
		self.refresh_ledger()
		self.balance_sheet()
		return self.start_date

	def set_txn(self, txn=None):
		self.txn = int(input('Enter a TXN ID: '))
		self.refresh_ledger()
		self.balance_sheet()
		return self.txn

	def refresh_ledger(self):
		self.df = pd.read_sql_query('SELECT * FROM ledger_' + self.ledger_name + ';', self.conn, index_col='txn_id')
		if self.entity != None: # TODO make able to select multiple entities
			self.df = self.df[(self.df.entity_id == self.entity)]
		if self.date != None:
			self.df = self.df[(self.df.date <= self.date)]
		if self.start_date != None:
			self.df = self.df[(self.df.date >= self.start_date)]
		if self.txn != None:
			self.df = self.df[(self.df.index <= self.txn)] # TODO Add start txn and event range
		return self.df

	def print_gl(self):
		self.refresh_ledger() # Refresh Ledger
		with pd.option_context('display.max_rows', None, 'display.max_columns', None): # To display all the rows
			print (self.df)
		print ('-' * DISPLAY_WIDTH)
		return self.df

	def get_acct_elem(self, acct):
		if acct in ['Asset','Liability','Wealth','Revenue','Expense','None']:
			return acct
		else:
			return self.get_acct_elem(Accounts.df.loc[acct, 'child_of'])

	def balance_sheet(self, accounts=None): # TODO Needs to be optimized
		all_accts = False
		#accounts=['Wealth']
		if accounts is None: # Create a list of all the accounts
			all_accts = True
			debit_accts = pd.unique(self.df['debit_acct'])
			credit_accts = pd.unique(self.df['credit_acct'])
			accounts = list( set(debit_accts) | set(credit_accts) )
		account_details = []

		# Create a list of tuples for all the accounts with their fundamental accounting element (asset,liab,eq,rev,exp)
		for acct in accounts:
			elem = self.get_acct_elem(acct)
			account_elem = (acct, elem)
			account_details.append(account_elem)

		# Group all the accounts together in lists based on their fundamental account element
		accounts = None
		assets = []
		liabilities = []
		wealth = []
		revenues = []
		expenses = []
		for acct in account_details:
			if acct[1] == 'Asset':
				assets.append(acct[0])
			elif acct[1] == 'Liability':
				liabilities.append(acct[0])
			elif acct[1] == 'Wealth':
				wealth.append(acct[0])
			elif acct[1] == 'Revenue':
				revenues.append(acct[0])
			elif acct[1] == 'Expense':
				expenses.append(acct[0])
			else:
				continue

		# Create Balance Sheet dataframe to return
		self.bs = pd.DataFrame(columns=['line_item','balance'])

		# TODO The below repeated sections can probably be handled more elegantly

		asset_bal = 0
		for acct in assets:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				logging.debug('Asset Debit Error')
				debits = 0
			try:
				credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				logging.debug('Asset Crebit Error')
				credits = 0
			bal = debits - credits
			asset_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Assets:', 'balance':asset_bal}, ignore_index=True)

		liab_bal = 0
		for acct in liabilities:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				logging.debug('Liabilities Debit Error')
				debits = 0
			try:
				credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				logging.debug('Liabilities Crebit Error')
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			liab_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Liabilities:', 'balance':liab_bal}, ignore_index=True)

		wealth_bal = 0
		for acct in wealth:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				logging.debug('Wealth Debit Error')
				debits = 0
			try:
				credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				logging.debug('Wealth Crebit Error')
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			wealth_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Wealth:', 'balance':wealth_bal}, ignore_index=True)

		rev_bal = 0
		for acct in revenues:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				logging.debug('Revenues Debit Error')
				debits = 0
			try:
				credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				logging.debug('Revenues Crebit Error')
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			rev_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Revenues:', 'balance':rev_bal}, ignore_index=True)

		exp_bal = 0
		for acct in expenses:
			logging.debug('Account: {}'.format(acct))
			try:
				debits = self.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				logging.debug('Expenses Debit Error')
				debits = 0
			try:
				credits = self.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				logging.debug('Expenses Crebit Error')
				credits = 0
			bal = debits - credits
			exp_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Expenses:', 'balance':exp_bal}, ignore_index=True)

		retained_earnings = rev_bal - exp_bal
		self.bs = self.bs.append({'line_item':'Net Income:', 'balance':retained_earnings}, ignore_index=True)

		net_asset_value = asset_bal - liab_bal
		if net_asset_value == 0: # Two ways to calc NAV depending on accounts
			net_asset_value = wealth_bal + retained_earnings

		total_equity = net_asset_value + liab_bal
		self.bs = self.bs.append({'line_item':'Wealth+NI+Liab.:', 'balance':total_equity}, ignore_index=True)

		check = asset_bal - total_equity
		self.bs = self.bs.append({'line_item':'Balance Check:', 'balance':check}, ignore_index=True)

		self.bs = self.bs.append({'line_item':'Net Asset Value:', 'balance':net_asset_value}, ignore_index=True)

		if all_accts:
			if self.entity is None:
				self.bs.to_sql('balance_sheet', self.conn, if_exists='replace')
			else:
				self.bs.to_sql('balance_sheet_' + str(self.entity), self.conn, if_exists='replace')
		return net_asset_value

	def print_bs(self):
		self.balance_sheet() # Refresh Balance Sheet
		print (self.bs)
		print ('-' * DISPLAY_WIDTH)
		return self.bs

	def get_qty_txns(self, item=None, acct=None):
		if acct is None:
			acct = 'Investments' #input('Which account? ')
		# TODO if a reversal is reversed, it will still cause issues
		rvsl_txns = self.df[self.df['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of txns
		qty_txns = self.df[(self.df['item_id'] == item) & (((self.df['debit_acct'] == acct) & (self.df['credit_acct'] == 'Cash')) | ((self.df['credit_acct'] == acct) & (self.df['debit_acct'] == 'Cash'))) & (~self.df['event_id'].isin(rvsl_txns))] # TODO Add support for non-cash
		return qty_txns

	def get_qty(self, item=None, acct=None): # TODO Add logic to ignore rvsls
		if acct is None:
			acct = 'Investments' #input('Which account? ')
		if (item is None) or (item == ''): # Get qty for all items
			inventory = pd.DataFrame(columns=['item_id','qty'])
			item_ids = self.df['item_id'].replace('', np.nan, inplace=True)
			item_ids = self.df['qty'].replace('None', np.nan, inplace=True) # TODO This line may not be needed on a clean ledger
			item_ids = pd.unique(self.df['item_id'].dropna())
			for item in item_ids:
				logging.debug(item)
				qty_txns = self.get_qty_txns(item)
				logging.debug(qty_txns)
				try:
					debits = qty_txns.groupby(['debit_acct','credit_acct']).sum()['qty'][acct][['credit_acct'] == 'Cash']
					logging.debug(debits)
				except:
					logging.debug('Error debit')
					debits = 0
				try:
					credits = qty_txns.groupby(['credit_acct','debit_acct']).sum()['qty'][acct][['credit_acct'] == 'Cash']
					logging.debug(credits)
				except:
					logging.debug('Error credit')
					credits = 0
				qty = round(debits - credits, 2)
				inventory = inventory.append({'item_id':item, 'qty':qty}, ignore_index=True)
				inventory = inventory[(inventory.qty != 0)]

			if self.entity is None:
				inventory.to_sql('inventory', self.conn, if_exists='replace')
			else:
				inventory.to_sql('inventory_' + str(self.entity), self.conn, if_exists='replace')
			return inventory

		# Get qty for one item specified
		qty_txns = self.get_qty_txns(item)
		try:
			debits = qty_txns.groupby(['debit_acct','credit_acct']).sum()['qty'][acct][['credit_acct'] == 'Cash']
		except:
			logging.debug('Error debit')
			debits = 0
		try:
			credits = qty_txns.groupby(['credit_acct','debit_acct']).sum()['qty'][acct][['credit_acct'] == 'Cash']
		except:
			logging.debug('Error credit')
			credits = 0
		qty = round(debits - credits, 2)
		return qty

	# Used when booking journal entries to match related transactions
	def get_event(self):
		event_query = 'SELECT event_id FROM ledger_'+ self.ledger_name +' ORDER BY event_id DESC LIMIT 1;'
		cur = self.conn.cursor()
		cur.execute(event_query)
		event_id = cur.fetchone()
		cur.close()
		if event_id is None:
			event_id = 1
			return event_id
		else:
			return event_id[0] + 1

	def get_entity(self):
		if self.entity is None:
			entity = 1
		else:
			entity = self.entity
		return entity

	def journal_entry(self, journal_data = None):
		'''
			The heart of the whole system; this is how transactions are entered.
			journal_data is a list of transactions. Each transaction is a list
			of datapoints. This means an event with a single transaction
			would be encapsulated in as a single list within a list.
		'''
		cur = self.conn.cursor()
		if journal_data is None: # Manually enter a journal entry
			event = input('Enter an optional event_id: ')
			entity = input('Enter the entity_id: ')
			date_raw = input('Enter a date as format yyyy-mm-dd: ')
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
			desc = input('Enter a description: ') + ' [M]'
			item = input('Enter an optional item_id: ')
			price = input('Enter an optional price: ')
			qty = input('Enter an optional quantity: ')
			debit = input('Enter the account to debit: ')
			if debit not in Accounts.df.index:
				print ('\n' + debit + ' is not a valid account.')
				return
			credit = input('Enter the account to credit: ')
			if credit not in Accounts.df.index:
				print ('\n' + credit + ' is not a valid account.')
				return
			while True:
				amount = input('Enter the amount: ')
				# if amount.isdigit():
				# 	break
				# else:
				# 	continue
				try: # TODO Maybe change to regular expressions to prevent negatives
					x = float(amount)
					break
				except ValueError:
					continue
			
			if event == '':
				event = str(self.get_event())
			if entity == '':
				entity = str(self.get_entity())
			if date == 'NaT':
				date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
				date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
			if qty == '': # TODO No qty and price default needed now
				qty = 1
			if price == '':
				price = amount

			values = (event, entity, date, desc, item, price, qty, debit, credit, amount)
			cur.execute('INSERT INTO ledger_' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)

		else: # Create journal entries by passing data to the function
			for je in journal_data:
				event = str(je[0])
				entity = str(je[1])
				date = str(je[2])
				desc = str(je[3])
				item  = str(je[4])
				price = str(je[5])
				qty = str(je[6])
				debit = str(je[7])
				credit = str(je[8])
				amount = str(je[9])
				logging.debug(je)

				if event == '':
					event = str(self.get_event())
				if entity == '':
					entity = str(self.get_entity())
				if date == 'NaT':
					date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
					date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
				if qty == '': # TODO No qty and price default needed now
					qty = 1
				if price == '':
					price = amount

				values = (event, entity, date, desc, item, price, qty, debit, credit, amount)
				cur.execute('INSERT INTO ledger_' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)

		self.conn.commit()
		cur.close()
		self.refresh_ledger() # Ensures the df is in sync with the db
		self.balance_sheet() # Ensures the bs is in sync with the ledger
		self.get_qty() # Ensures the inv is in sync with the ledger

	def sanitize_ledger(self): # This is not implemented yet
		self.df = self.df.drop_duplicates() # TODO Test this

	def load_gl(self):
		infile = input('Enter a filename: ')
		with open(infile, 'r') as f:
			load_df = pd.read_csv(f, keep_default_na=False)
			load_df.set_index('txn_id', inplace=True)
			lol = load_df.values.tolist()
			print(load_df)
			print ('-' * DISPLAY_WIDTH)
			self.journal_entry(lol)
			#self.sanitize_ledger() # Not sure if I need this anymore

	def export_gl(self):
		outfile = 'ledger_' + self.ledger_name + '_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		self.df.to_csv(save_location + outfile, date_format='%Y-%m-%d')
		print ('File saved as ' + save_location + outfile + '\n')

	def reversal_entry(self, txn=None): # This func effectively deletes a transaction
		if txn is None:
			txn = input('Which txn_id to reverse? ')
		rvsl_query = 'SELECT * FROM ledger_'+ self.ledger_name +' WHERE txn_id = '+ txn + ';'
		cur = self.conn.cursor()
		cur.execute(rvsl_query)
		rvsl = cur.fetchone()
		cur.close()
		date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
		date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
		rvsl_entry = [[ rvsl[1], rvsl[2], date, '[RVSL]' + rvsl[4], rvsl[5], rvsl[6], rvsl[7], rvsl[9], rvsl[8], rvsl[10] ]]
		self.journal_entry(rvsl_entry)

	def hist_cost(self, qty, item=None, acct=None):
		if acct is None:
			acct = 'Investments' #input('Which account? ')

		qty_txns = self.get_qty_txns(item, acct)['qty']

		# Find the first lot of unsold items
		count = 0
		qty_back = self.get_qty(item, acct)
		for item in qty_txns[::-1]:
			if qty_back <= 0:
				break
			count -= 1
			qty_back -= item

		start_qty = qty_txns.iloc[count]
		start_index = qty_txns.index[count]
		avail_qty = qty_back + start_qty # Portion of first lot of unsold items that has not been sold

		amount = 0
		if qty <= avail_qty: # Case when first available lot covers the need
			price_chart = pd.DataFrame({'price':[self.df.loc[start_index]['price']],'qty':[qty]})
			amount = price_chart.price.dot(price_chart.qty)
			logging.debug('Hist Cost Case: One')
			logging.debug(amount)
			return amount

		price_chart = pd.DataFrame({'price':[self.df.loc[start_index]['price']],'qty':[avail_qty]}) # Create a list of lots with associated price
		qty = qty - avail_qty # Sell the remainer of first lot of unsold items

		count += 1
		for item in qty_txns[count::-1]:
			current_index = qty_txns.index[count]
			while qty > 0: # Running amount of qty to be sold
				count += 1
				if qty - self.df.loc[current_index]['qty'] < 0: # Final case when the last sellable lot is larger than remaining qty to be sold
					price_chart = price_chart.append({'price':self.df.loc[current_index]['price'], 'qty':qty}, ignore_index=True)
					amount = price_chart.price.dot(price_chart.qty)
					logging.debug('Hist Cost Case: Two')
					logging.debug(amount)
					return amount
				
				price_chart = price_chart.append({'price':self.df.loc[current_index]['price'], 'qty':self.df.loc[current_index]['qty']}, ignore_index=True)
				qty = qty - self.df.loc[current_index]['qty']

			amount = price_chart.price.dot(price_chart.qty) # Take dot product
			logging.debug('Hist Cost Case: Three')
			logging.debug(amount)
			return amount

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	args = parser.parse_args()

	accts = Accounts(conn=args.database)
	ledger = Ledger(ledger_name=args.ledger,entity=args.entity)

	while True:
		command = input('\nType one of the following commands:\nBS, GL, JE, RVSL, loadGL, exportGL, Accts, loadAccts, addAcct, exit\n')
		if command.lower() == 'exit':
			exit() # TODO Add help command to list full list of commands
		elif command.lower() == 'gl':
			ledger.print_gl()
		elif command.lower() == 'exportgl':
			ledger.export_gl()
		elif command.lower() == 'loadgl':
			ledger.load_gl()
		elif command.lower() == 'accts':
			accts.print_accts()
		elif command.lower() == 'addacct':
			accts.add_acct()
		elif command.lower() == 'removeacct':
			accts.remove_acct()
		elif command.lower() == 'loadaccts':
			accts.load_accts()
		elif command.lower() == 'exportaccts':
			accts.export_accts()
		elif command.lower() == 'dupes':
			accts.drop_dupe_accts()
		elif command.lower() == 'je':
			ledger.journal_entry()
		elif command.lower() == 'rvsl':
			ledger.reversal_entry()
		elif command.lower() == 'bs':
			ledger.print_bs()
		elif command.lower() == 'qty':
			item = input('Which ticker? ').lower()
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print (ledger.get_qty(item))
		elif command.lower() == 'entity':
			ledger.set_entity()
		elif command.lower() == 'date':
			ledger.set_date()
		elif command.lower() == 'startdate':
			ledger.set_start_date()
		elif command.lower() == 'txn':
			ledger.set_txn()
		else:
			print('Not a valid command. Type exit to close.')