import logging
logger = logging.getLogger(__name__)
import logging
from kiteconnect import KiteTicker
from time import sleep
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
		self.global_data = dict()		#price or volume only
		self.strat_data = dict()		#indicator 1 & 2 , status, etc
		self.tick_count, self.min_count = 1, 0

		self.time_map = {'minute' : 1, 'day' : 30, '3minute' : 2, '5minute' : 3, '10minute' : 5, '15minute' : 7, '30minute' : 10 , '60minute' : 15}

		
		print('###BLOCK 1')
		for s in self.strat_list:
			t = int(s.instrument)
			self.tokens.append(t)
			self.global_data[t] = dict.fromkeys(['price', 'volume'])
			self.strat_data[s.pk] = dict({'status' : False})
			s.indicator1 = s.indicator1.down_cast()
			s.indicator2 = s.indicator2.down_cast()

		self.tokens = list(set(self.tokens))		#repeated tokens || multiple strategies on single instrument
			
		print('###BLOCK 2')
		self.kf = KiteFetcher(self.access_token)
		self.update_indicators(self.strat_list)

		print('MY_INIT : Gloal data :- ' + str(self.global_data))



	def strat_refresh(self):
		print("Strat_Refresh method called...")
		old_strat_list = self.strat_list
		self.strat_list = Strategy.objects.all()
		self.tokens.clear()
		pk_list = list()

		for s in self.strat_list:
			s.indicator1 = s.indicator1.down_cast()
			s.indicator2 = s.indicator2.down_cast()
			self.tokens.append(int(s.instrument))
			pk_list.append(s.pk)
		self.tokens = list(set(self.tokens))

		new_global_data = dict(self.global_data)
		for k in self.global_data.keys():
			if(k not in self.tokens):
				_ = new_global_data.pop(k, None)
		self.global_data = new_global_data

		new_strat_data = dict(self.strat_data)
		for k in self.strat_data.keys():
			if(k not in pk_list):
				_ = new_strat_data.pop(k, None)
		self.strat_data = new_strat_data


		strats_to_update = list()
		for s in self.strat_list:
			if(s not in old_strat_list):
				t = int(s.instrument)
				if(t not in self.global_data.keys()):
					self.global_data[t] = dict.fromkeys(['price','volume'])

				self.strat_data[s.pk] = dict({'status' : False})
				strats_to_update.append(s)

		self.update_indicators(strats_to_update)
		print("Strategies updated successfully")



	def update_indicators(self, strats_to_update):
		min_count += 1
		t = Timer(45, self.update_indicators)		#45 sec timer equivalent to 1 minute with code execution
		t.start()

		for s in strats_to_update:
			if(s.indicator1.name not in ['price', 'volume']):
				if(min_count % self.time_map[s.indicator1.interval]  ==  0):
					self.strat_data[s.pk]['indicator1'] = s.indicator1.evaluate(kite_fetcher = self.kf, instrument = int(s.instrument))

			if(s.indicator2.name not in ['price', 'volume']):
				if(min_count % self.time_map[s.indicator2.interval]  ==  0):
					self.strat_data[s.pk]['indicator2'] = s.indicator2.evaluate(kite_fetcher = self.kf, instrument = int(s.instrument))		


	def strategy_status(self, s):
		if(s.indicator1.name in ['price', 'volume']):
			self.strat_data[s.pk]['indicator1'] = self.global_data[int(s.instrument)][s.indicator1.name]
		indicator1 = self.strat_data[s.pk]['indicator1']

		if(s.indicator2.name in ['price', 'volume']):
			self.strat_data[s.pk]['indicator2'] = self.global_data[int(s.instrument)][s.indicator2.name]
		indicator2 = self.strat_data[s.pk]['indicator2']

		c = int(s.comparator)
		if(c == 1):		#greater than
			if(indicator1 > indicator2):
				return True

		else if(c == 2):	#less than
			if(indicator1 < indicator2):
				return True

		else if(c == 3):	#crosses above
			if(self.strat_data[s.pk]['status']==False and  indicator1 > indicator2):
				return True

		else if(c == 4):	#crosses below
			if(self.strat_data[s.pk]['status']==False and  indicator1 < indicator2):
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

				self.strat_data[s.pk]['status'] = self.strategy_status(s)

				strategy_meta[str(s)] = {
					'status' : self.strat_data[s.pk]['status'],
					'price' : self.global_data[t]['price'],
					'volume' : self.global_data[t]['volume'],
					'indicator 1' : str(self.strat_data[s.pk]['indicator1']) + "("+ str(s.indicator1) +")" ,
					'indicator 2' : str(self.strat_data[s.pk]['indicator2']) + "("+ str(s.indicator2) +")" 
				}

			self.task.update_state(state='PROGRESS', meta=strategy_meta)
			print(strategy_meta)

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