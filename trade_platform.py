from acct import Accounts
from acct import Ledger
import urllib.request
from time import strftime, localtime

class Trading(object):
	def get_price(self, symbol):
		url = 'https://api.iextrading.com/1.0/stock/'
		try:
			price = float(urllib.request.urlopen(url + symbol + '/price').read())
		except:
			print ('Error getting price from: ' + url + symbol + '/price')
		else:
			return price #round(price, 2)

	def date(self):
		return strftime('%Y-%m-%d', localtime())

	def com(self):
		com = 9.95
		return com

	def buy_shares(self, symbol, qty=1):
		if qty == 1:
			qty = int(input('How many shares? '))
		price = self.get_price(symbol)

		# Check if there is enough capital
		capital_accts = ['Cash','Chequing']
		capital_bal = 0
		#capital_bal = ledger.balance_sheet(capital_accts) # TODO Fix this!

		for acct in capital_accts: # TODO Remove this for balance_sheet() function when it works properly
			try:
				debits = ledger.df.groupby('debit_acct').sum()['amount'][acct]
			except:
				debits = 0
				print ('Debit error!')
			try:
				credits = ledger.df.groupby('credit_acct').sum()['amount'][acct]
			except:
				credits = 0
				print ('Credit error!')
			bal = round(debits - credits, 2)
			capital_bal += bal

		if price * qty > capital_bal:
			print ('\nBuying ' + str(qty) + ' shares of ' + symbol + ' costs $' + str(round(price * qty, 2)) + '.')
			print ('You currently have $' + str(capital_bal) + ' available.\n')
			return

		# TODO Decide whether to display unrealized gains as temp entries with rvsls or not
		# Journal entries for a buy transaction
		buy_entry = [ ledger.get_event(), ledger.get_entity(), self.date(), 'Shares buy', symbol, price, qty, 'Investments', 'Cash', price * qty]
		com_entry = [ ledger.get_event(), ledger.get_entity(), self.date(), 'Comm. buy', '', trade.com(), 1, 'Commission Expense', 'Cash', trade.com()]
		buy_event = [buy_entry, com_entry]

		ledger.journal_entry(buy_event)

	def sell_shares(self, symbol, qty=1):
		if qty == 1:
			qty = int(input('How many shares? '))
		current_qty = ledger.get_qty(symbol, 'Investments')
		if qty > current_qty:
			print ('You currently have ' + str(current_qty) + ' shares.')
			return

		# Calculate profit
		price = self.get_price(symbol)
		sale_proceeds = qty * price
		hist_cost = ledger.hist_cost(qty, symbol, 'Investments')
		investment_gain = None
		investment_loss = None
		if sale_proceeds >= hist_cost:
			investment_gain = sale_proceeds - hist_cost
		else:
			investment_loss = hist_cost - sale_proceeds

		# Journal entries for a sell transaction
		sell_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Shares sell', symbol, hist_cost / qty, qty, 'Cash', 'Investments', hist_cost]
		if investment_gain is not None:
			profit_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Realized gain', '', price, 1, 'Cash', 'Investment Gain', investment_gain]
		if investment_loss is not None:
			profit_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Realized loss', '', price, 1, 'Investment Loss', 'Cash', investment_loss]
		com_entry = [ ledger.get_event(), ledger.get_entity(), trade.date(), 'Comm. sell', '', trade.com(), 1,'Commission Expense', 'Cash', trade.com()]
		sell_event = [sell_entry, profit_entry, com_entry]

		ledger.journal_entry(sell_event)

if __name__ == '__main__':
	accts = Accounts()
	ledger = Ledger('test_1')
	#ledger = Ledger(accts, 'test_1') # My attempt to fix my issue
	trade = Trading()

	# TODO add command to list tickers
	while True:
		command = input('\nType one of the following commands:\nbuy, sell, exit\n')
		if command.lower() == 'exit':
			exit()
		elif command.lower() == 'buy':
			symbol = input('Which ticker? ')
			trade.buy_shares(symbol)
		elif command.lower() == 'sell':
			symbol = input('Which ticker? ')
			trade.sell_shares(symbol)
		else:
			print('Not a valid command. Type exit to close.')