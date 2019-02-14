import time
import logging
logger = logging.getLogger(__name__)
import logging
from kiteconnect import KiteTicker
from time import sleep
import time
import pandas as pd
import datetime
from threading import Timer
from .models import Strategy, Refreshed
from .indicators import KiteFetcher
import os

class Work(object):

	def __init__(self, task):
		self.task = task
		print('MY_INIT METHOD CALLED '+str(self.task.request.id))		

		path = os.getcwd() + '/blog/extras/task.csv'
		df = pd.read_csv(path, index_col=False)		
		df['task_id'] = self.task.request.id
		self.access_token = str(df['access_token'][0])
		df.to_csv(path, index=False)

		self.strat_list = Strategy.objects.all()		
		self.tokens = list()	
		self.global_data = dict()
		self.tick_count = 1
		
		print('###BLOCK 1')
		for s in self.strat_list:
			t = int(s.instrument)
			self.tokens.append(t)
			self.global_data[t] = dict()

		self.tokens = list(set(self.tokens))		#repeated tokens || multiple strategies on single instrument

		for s in self.strat_list:
			self.global_data[int(s.instrument)][s.indicator1] = None
			self.global_data[int(s.instrument)][s.indicator2] = None
			

		print('###BLOCK 2')
		self.kf = KiteFetcher(self.access_token)
		self.update_indicators(self.tokens)

		print('MY_INIT : Gloal data :- ' + str(self.global_data))



	def strat_refresh(self):
		print("Strat_Refresh method called...")
		old_strat_list = self.strat_list
		self.strat_list = Strategy.objects.all()
		self.tokens.clear()

		for s in self.strat_list:
			self.tokens.append(int(s.instrument))
		self.tokens = list(set(self.tokens))

		new_global_data = dict(self.global_data)
		for k in self.global_data.keys():
			if(k not in self.tokens):
				_ = new_global_data.pop(k, None)
		self.global_data = new_global_data


		indicators_to_update = list()
		for s in self.strat_list:
			if(s not in old_strat_list):
				t = int(s.instrument)
				if(int(s.instrument) not in self.global_data.keys()):
					self.global_data[t] = dict()

				self.global_data[t][s.indicator1] = None
				self.global_data[t][s.indicator2] = None
				indicators_to_update.append(t)

		self.update_indicators(indicators_to_update)
		print("Strategies updated successfully")





	def update_indicators(self, passed_tokens):
		for t in passed_tokens:
			indi_list = list(self.global_data[t].keys())
			update = self.kf.get_passed_indicators(t, list(indi_list))

			for i in indi_list:
				if(i == 'price' or i == 'volume'):
					pass
				else:
					self.global_data[t][i] = update[i]


	def strategy_status(self, s):
		inst = int(s.instrument)
		indicator1 = self.global_data[inst][s.indicator1]
		indicator2 = self.global_data[inst][s.indicator2]

		if(int(s.comparator) == 1):		#greater than
			if(indicator1 > indicator2):
				return True
		else:
			if(indicator1 <= indicator2):
				return True
		
		return False


	def run(self):      
		tokens = self.tokens
		# kws = KiteTicker('0ld4qxtvnif715ls', 'rCbSsBUalr9wHT2hiIZ30ArWFuvD9mFZ')
		kws = KiteTicker('0ld4qxtvnif715ls', self.access_token)

		def stop_gracefully():
			kws.stop_retry()
			kws.close()
			print('____________________Closed KiteTicker Gracefully_________________')
		
						  
		def on_ticks(ws, ticks):
			print('\n______________________________ON TICKS_____________________________\n')
			# self.tick_count += 1
			for i in ticks:		
				t = i['instrument_token']
				self.global_data[t]['price'] = i['last_price']
				self.global_data[t]['volume'] = i['volume']

			strategy_meta = dict()
			for s in self.strat_list:
				t = int(s.instrument)

				strategy_meta[str(s)] = {
					'status' : self.strategy_status(s),
					'price' : self.global_data[t]['price'],
					'volume' : self.global_data[t]['volume'],
					'indicator 1' : str(self.global_data[t][s.indicator1]) + "("+ s.indicator1 +")" ,
					'indicator 2' : str(self.global_data[t][s.indicator2]) + "("+ s.indicator2 +")" 
				}

			self.task.update_state(state='PROGRESS', meta=strategy_meta)
			# print(strategy_meta)

			if(self.tick_count == 0):
				r = Refreshed.objects.all().filter(name = 'Strategy')
				if(len(r) > 0):		#Strategies were modified
					print("\nRefreshing needed.....")
					stop_gracefully()
					self.strat_refresh()
					self.run()
					r.delete()
					print("_______________Deleted refresh objects__________________")

			self.tick_count = (self.tick_count + 1)%10
			
						  

		def on_connect(ws, response):
			logging.info("Successfully connected. Response: {}".format(response))
			ws.subscribe(tokens)
			ws.set_mode(ws.MODE_FULL, tokens)
			print("Subscribe to tokens in Full mode: {}".format(tokens))


		def on_close(ws, code, reason):
			print("Connection closed: {code} - {reason}".format(code=code, reason=reason))
			# print("Connection closed")


		def on_error(ws, code, reason):
			print("Connection error: {code} - {reason}".format(code=code, reason=reason))
			# print("Connection Error")


		def on_reconnect(ws, attempts_count):
			# logging.info("Reconnecting: {}".format(attempts_count))
			print("Reconnecting")


		def on_noreconnect(ws):
			print("Reconnect failed.")            
		

		kws.on_ticks = on_ticks
		kws.on_close = on_close
		kws.on_error = on_error
		kws.on_connect = on_connect
		kws.on_reconnect = on_reconnect
		kws.on_noreconnect = on_noreconnect

		kws.connect(threaded=False)