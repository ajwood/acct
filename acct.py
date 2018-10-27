import pandas as pd
import numpy as np
import sqlite3
import argparse
import datetime
import logging

DISPLAY_WIDTH = 97
pd.set_option('display.width', DISPLAY_WIDTH)
pd.options.display.float_format = '${:,.2f}'.format
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

class Accounts(object):
	def __init__(self, conn=None):
		if conn is None:
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
				website = True
				logging.debug('Website: {}'.format(website))
			except:
				conn = sqlite3.connect('db/acct.db')
				website = False
				logging.debug('Website: {}'.format(website))
		elif isinstance(conn, str):
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/' + conn)
				website = True
				logging.debug('Website: {}'.format(website))
			except:
				conn = sqlite3.connect('db/' + conn)
				website = False
				logging.debug('Website: {}'.format(website))
		else:
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
				website = True
				logging.debug('Website: {}'.format(website))
			except:
				conn = sqlite3.connect('db/acct.db')
				website = False
				logging.debug('Website: {}'.format(website))

		Accounts.conn = conn

		try:
			self.refresh_accts()
		except:
			Accounts.df = None
			self.create_accts()
			self.refresh_accts()
			self.create_entities()
			self.create_items()

	def create_accts(self):
		create_accts_query = '''
			CREATE TABLE IF NOT EXISTS accounts (
				accounts text,
				child_of text
			);
			'''
		standard_accts = [
			('Account','None'),
			('Admin','Account'),
			('Asset','Account'),
			('Equity','Account'),
			('Liability','Equity'),
			('Wealth','Equity'),
			('Revenue','Wealth'),
			('Expense','Wealth'),
			('Transfer','Wealth')
		]

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

	def create_entities(self): # TODO Add command to book more entities
		create_entities_query = '''
			CREATE TABLE IF NOT EXISTS entities (
				entity_id INTEGER PRIMARY KEY,
				name text,
				comm real DEFAULT 0,
				min_qty INTEGER NOT NULL,
				max_qty INTEGER NOT NULL,
				liquidate_chance real NOT NULL,
				ticker_source text DEFAULT 'iex'
			);
			'''
		default_entities = ['''
			INSERT INTO entities (
				name,
				comm,
				min_qty,
				max_qty,
				liquidate_chance,
				ticker_source
				)
				VALUES (
					'Trader01',
					0.0,
					1,
					100,
					0.5,
					'iex'
				);
			''']

		cur = self.conn.cursor()
		cur.execute(create_entities_query)
		for entity in default_entities:
				print('Entities created.')
				cur.execute(entity)
		self.conn.commit()
		cur.close()

	def create_items(self):# TODO Add command to book more items
		create_items_query = '''
			CREATE TABLE IF NOT EXISTS items (
				item_id text PRIMARY KEY,
				int_rate_fix real,
				int_rate_var real,
				freq integer DEFAULT 365
			);
			'''
		default_item = ['''
			INSERT INTO items (
				item_id,
				int_rate_fix,
				int_rate_var,
				freq
				) VALUES (
					'credit_line_01',
					0.0409,
					NULL,
					365
				);
			''']

		cur = self.conn.cursor()
		cur.execute(create_items_query)
		for item in default_item:
				print('Items created.')
				cur.execute(item)
		self.conn.commit()
		cur.close()

	def refresh_accts(self):
		Accounts.df = pd.read_sql_query('SELECT * FROM accounts;', self.conn, index_col='accounts')

	def print_accts(self):
		self.refresh_accts()
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print (Accounts.df)
		print('-' * DISPLAY_WIDTH)
		return Accounts.df

	def drop_dupe_accts(self):
		Accounts.df = Accounts.df[~Accounts.df.index.duplicated(keep='first')]
		Accounts.df.to_sql('accounts', self.conn, if_exists='replace')
		self.refresh_accts()

	def add_acct(self, acct_data=None):
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

	def load_accts(self, infile=None):
		if infile is None:
			infile = input('Enter a filename: ')
		if infile == 'trading': # Workaround due to an app limitation
			trade_accts = [
				('Cash','Asset'),
				('Chequing','Asset'),
				('Savings','Asset'),
				('Investments','Asset'),
				('Visa','Liability'),
				('Student Credit','Liability'),
				('Credit Line','Liability'),
				('Uncategorized','Admin'),
				('Info','Admin'),
				('Commission Expense','Expense'),
				('Investment Gain','Revenue'),
				('Investment Loss','Expense'),
				('Unrealized Gain','Revenue'),
				('Unrealized Loss','Expense'),
				('Interest Expense','Expense'),
				('Dividend Receivable','Asset'),
				('Dividend Income','Revenue'),
				('Interest Income','Revenue')
			]
			self.add_acct(trade_accts)
			return
		with open(infile, 'r') as f:
			load_df = pd.read_csv(f, keep_default_na=False)
			lol = load_df.values.tolist()
			print(load_df)
			print('-' * DISPLAY_WIDTH)
			self.add_acct(lol)

	def export_accts(self):
		outfile = 'accounts_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		Accounts.df.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
		print('File saved as ' + save_location + outfile + '\n')

	def remove_acct(self, acct=None):
		if acct is None:
			acct = input('Which account would you like to remove? ')
		cur = self.conn.cursor()
		cur.execute('DELETE FROM accounts WHERE accounts=?', (acct,))
		self.conn.commit()
		cur.close()
		self.refresh_accts()

	def print_entities(self): # TODO Add error checking if no entities exist
		self.entities = pd.read_sql_query('SELECT * FROM entities;', self.conn, index_col=['entity_id'])
		self.entities.to_csv('data/entities.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.entities)
		print('-' * DISPLAY_WIDTH)
		return self.entities

	def print_items(self): # TODO Add error checking if no items exist
		self.items = pd.read_sql_query('SELECT * FROM items;', self.conn, index_col=['item_id'])
		self.items.to_csv('data/items.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.items)
		print('-' * DISPLAY_WIDTH)
		return self.items


class Ledger(Accounts):
	def __init__(self, ledger_name=None, entity=None, date=None, start_date=None, txn=None):
		self.conn = Accounts.conn
		if ledger_name is None:
			self.ledger_name = 'gen_ledger'
		else:
			self.ledger_name = ledger_name
		self.entity = entity
		self.date = date
		self.start_date = start_date
		self.txn = txn
		self.create_ledger()
		self.refresh_ledger() # TODO Make this self.df = self.refresh_ledger()
		self.balance_sheet()
			
	def create_ledger(self): # TODO Change entity_id to string type
		create_ledger_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.ledger_name + ''' (
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
		if entity is None:
			self.entity = int(input('Enter an Entity ID: ')) # TODO Change entity_id to string type
		else:
			self.entity = entity
		self.refresh_ledger()
		self.balance_sheet()
		return self.entity

	def set_date(self, date=None):
		if date is None:
			self.date = input('Enter a date in format YYYY-MM-DD: ')
		else:
			self.date = date
		self.refresh_ledger()
		self.balance_sheet()
		return self.date

	def set_start_date(self, start_date=None):
		if start_date is None:
			self.start_date = input('Enter a date in format YYYY-MM-DD: ')
		else:
			self.start_date = start_date
		self.refresh_ledger()
		self.balance_sheet()
		return self.start_date

	def set_txn(self, txn=None):
		if txn is None:
			self.txn = int(input('Enter a TXN ID: '))
		else:
			self.txn = txn
		self.refresh_ledger()
		self.balance_sheet()
		return self.txn

	# TODO Add set_start_txn() function

	def reset(self):
		self.entity = None
		self.date = None
		self.start_date = None
		self.txn = None
		self.refresh_ledger()
		self.balance_sheet()

	def refresh_ledger(self):
		self.df = pd.read_sql_query('SELECT * FROM ' + self.ledger_name + ';', self.conn, index_col='txn_id')
		if self.entity is not None: # TODO make able to select multiple entities
			self.df = self.df[(self.df.entity_id == self.entity)]
		if self.date is not None:
			self.df = self.df[(self.df.date <= self.date)]
		if self.start_date is not None:
			self.df = self.df[(self.df.date >= self.start_date)]
		if self.txn is not None:
			self.df = self.df[(self.df.index <= self.txn)] # TODO Add start txn and event range
		return self.df

	def print_gl(self):
		self.refresh_ledger() # Refresh Ledger
		#with pd.option_context('display.max_rows', None, 'display.max_columns', None): # To display all the rows
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
		self.bs = pd.DataFrame(columns=['line_item','balance']) # TODO Make line_item the index

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
		rvsl_txns = self.df[self.df['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of txns
		qty_txns = self.df[(self.df['item_id'] == item) & (((self.df['debit_acct'] == acct) & (self.df['credit_acct'] == 'Cash')) | ((self.df['credit_acct'] == acct) & (self.df['debit_acct'] == 'Cash'))) & (~self.df['event_id'].isin(rvsl_txns))] # TODO Add support for non-cash
		return qty_txns

	def get_qty(self, item=None, acct=None):
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
				inventory = inventory[(inventory.qty != 0)] # Ignores items completely sold # TODO Add arg flag to turn this off for divs

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
		event_query = 'SELECT event_id FROM ' + self.ledger_name +' ORDER BY event_id DESC LIMIT 1;'
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

	def journal_entry(self, journal_data=None):
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
			cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)

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
				#print(values)
				cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', values)

		self.conn.commit()
		cur.close()
		self.refresh_ledger() # Ensures the df is in sync with the db
		self.balance_sheet() # Ensures the bs is in sync with the ledger
		self.get_qty() # Ensures the inv is in sync with the ledger

	def sanitize_ledger(self): # This is not implemented yet
		self.df = self.df.drop_duplicates() # TODO Test this

	def load_gl(self, infile=None):
		if infile is None:
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
		self.reset()
		outfile = self.ledger_name + '_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		self.df.to_csv(save_location + outfile, date_format='%Y-%m-%d')
		print ('File saved as ' + save_location + outfile)

	def reversal_entry(self, txn=None, date=None): # This func effectively deletes a transaction
		if txn is None:
			txn = input('Which txn_id to reverse? ')
		rvsl_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';'
		cur = self.conn.cursor()
		cur.execute(rvsl_query)
		rvsl = cur.fetchone()
		logging.debug('rvsl: {}'.format(rvsl))
		cur.close()
		if '[RVSL]' in rvsl[4]:
			print('Cannot reverse a reversal. Enter a new entry instead.')
			return
		if date is None:
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
		qty_back = self.get_qty(item, acct) # TODO Confirm this work when there are multiple different lots of buys and sell in the past
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
		qty = qty - avail_qty # Sell the remainder of first lot of unsold items

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

	def bs_hist(self): # TODO Optimize this so it does not recalculate each time
		gl_entities = pd.unique(self.df['entity_id'])
		logging.info(gl_entities)
		dates = pd.unique(self.df['date'])
		logging.info(dates)

		cur = self.conn.cursor()
		create_bs_hist_query = '''
			CREATE TABLE IF NOT EXISTS hist_bs (
				date date NOT NULL,
				entity text NOT NULL,
				assets real NOT NULL,
				liabilities real NOT NULL,
				wealth real NOT NULL,
				revenues real NOT NULL,
				expenses real NOT NULL,
				net_income real NOT NULL,
				wealth_ni_liab real NOT NULL,
				bal_check real NOT NULL,
				net_asset_value real NOT NULL
			);
			'''
		cur.execute(create_bs_hist_query)
		cur.execute('DELETE FROM hist_bs')
		for entity in gl_entities:
			logging.info(entity)
			ledger.set_entity(entity)
			for date in dates:
				logging.info(entity)
				ledger.set_date(date)
				logging.info(date)
				ledger.balance_sheet()
				self.bs.set_index('line_item', inplace=True)
				col0 = str(entity)
				col1 = self.bs.loc['Total Assets:'][0]
				col2 = self.bs.loc['Total Liabilities:'][0]
				col3 = self.bs.loc['Total Wealth:'][0]
				col4 = self.bs.loc['Total Revenues:'][0]
				col5 = self.bs.loc['Total Expenses:'][0]
				col6 = self.bs.loc['Net Income:'][0]
				col7 = self.bs.loc['Wealth+NI+Liab.:'][0]
				col8 = self.bs.loc['Balance Check:'][0]
				col9 = self.bs.loc['Net Asset Value:'][0]
				
				data = (date,col0,col1,col2,col3,col4,col5,col6,col7,col8,col9)
				logging.info(data)
				cur.execute('INSERT INTO hist_bs VALUES (?,?,?,?,?,?,?,?,?,?,?)', data)
		self.conn.commit()
		cur.execute('PRAGMA database_list')
		db_path = cur.fetchall()[0][-1]
		db_name = db_path.rsplit('/', 1)[-1]
		cur.close()

		self.hist_bs = pd.read_sql_query('SELECT * FROM hist_bs;', self.conn, index_col=['date','entity'])
		return self.hist_bs, db_name

		# TODO Add function to book just the current days bs to hist_bs

	def print_hist(self):
		db_name = self.bs_hist()[1]
		path = 'data/bs_hist_' + db_name[:-3] + '.csv'
		self.hist_bs.to_csv(path, index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None): # To display all the rows
			print(self.hist_bs)
		print('File saved to: {}'.format(path))
		print ('-' * DISPLAY_WIDTH)
		return self.hist_bs


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-c', '--command', type=str, help='A command for the program.')
	args = parser.parse_args()

	accts = Accounts(conn=args.database)
	ledger = Ledger(ledger_name=args.ledger, entity=args.entity)
	command = args.command

	while True:
		if args.command is None:
			command = input('\nType one of the following commands:\nBS, GL, JE, RVSL, loadGL, exportGL, Accts, loadAccts, addAcct, exit\n')
		# TODO Add help command to list full list of commands
		if command.lower() == 'gl':
			ledger.print_gl()
			if args.command is not None: exit()
		elif command.lower() == 'exportgl':
			ledger.export_gl()
			if args.command is not None: exit()
		elif command.lower() == 'loadgl':
			ledger.load_gl()
			if args.command is not None: exit()
		elif command.lower() == 'accts':
			accts.print_accts()
			if args.command is not None: exit()
		elif command.lower() == 'addacct':
			accts.add_acct()
			if args.command is not None: exit()
		elif command.lower() == 'removeacct':
			accts.remove_acct()
			if args.command is not None: exit()
		elif command.lower() == 'loadaccts':
			accts.load_accts()
			if args.command is not None: exit()
		elif command.lower() == 'exportaccts':
			accts.export_accts()
			if args.command is not None: exit()
		elif command.lower() == 'dupes':
			accts.drop_dupe_accts()
			if args.command is not None: exit()
		elif command.lower() == 'je':
			ledger.journal_entry()
			if args.command is not None: exit()
		elif command.lower() == 'rvsl':
			ledger.reversal_entry()
			if args.command is not None: exit()
		elif command.lower() == 'bs':
			ledger.print_bs()
			if args.command is not None: exit()
		elif command.lower() == 'qty':
			item = input('Which ticker? ').lower()
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print (ledger.get_qty(item))
			if args.command is not None: exit()
		elif command.lower() == 'entity':
			ledger.set_entity()
			if args.command is not None: exit()
		elif command.lower() == 'date':
			ledger.set_date()
			if args.command is not None: exit()
		elif command.lower() == 'startdate':
			ledger.set_start_date()
			if args.command is not None: exit()
		elif command.lower() == 'txn':
			ledger.set_txn()
			if args.command is not None: exit()
		elif command.lower() == 'reset':
			ledger.reset()
			if args.command is not None: exit()
		elif command.lower() == 'hist':
			ledger.print_hist()
			if args.command is not None: exit()
		elif command.lower() == 'entities':
			accts.print_entities()
			if args.command is not None: exit()
		elif command.lower() == 'items':
			accts.print_items()
			if args.command is not None: exit()
		elif command.lower() == 'width': # TODO Try and make this work
			DISPLAY_WIDTH = int(input('Enter number for display width: '))
			if args.command is not None: exit()
		elif command.lower() == 'exit' or args.command is not None:
			exit()
		else:
			print('Not a valid command. Type exit to close.')
# New test branch comment
