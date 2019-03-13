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
import numpy as np
import blog.extras.access_token as AT

class Work(object):

	def __init__(self, task):
		self.task = task
		print('MY_INIT METHOD CALLED '+str(self.task.request.id))		
		
		self.time_stamp = pd.Timestamp('today').minute		#for maintaining recent candle's OHLC
		self.access_token = AT.get_access_token()
		AT.set_task_id(self.task.request.id)

		self.strat_list = Strategy.objects.all()		
		self.tokens = list()	
		self.global_data = dict()		#price or volume only
		self.strat_data = dict()		#indicator 1 & 2 , status, etc
		self.tick_count, self.min_count = 1, 0

		self.time_map = {'minute' : 1, 'day' : 13, '3minute' : 1, '5minute' : 1, '10minute' : 1, '15minute' : 2, '30minute' : 3 , '60minute' : 4}

		
		print('###BLOCK 1')
		for s in self.strat_list:
			t = int(s.instrument)
			self.tokens.append(t)
			self.global_data[t] = dict({'price':0, 'volume':0})		#'price' == 'close'
			self.strat_data[s.pk] = dict({'status' : False, 'indicator1':0, 'indicator2':0, 'timestamp':pd.Timestamp('today')})
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
					self.global_data[t] = dict({'price':0, 'volume':0})

				self.strat_data[s.pk] = dict({'status' : False, 'indicator1':0, 'indicator2':0, 'timestamp':pd.Timestamp('today')})
				strats_to_update.append(s)

		self.update_indicators(strats_to_update, force=True)
		print("Strategies updated successfully")



	def update_indicators(self, strats_to_update, force=False):		
		t = Timer(np.round(len(strats_to_update)/3 +1), self.update_indicators, [strats_to_update])		#45 sec timer equivalent to 1 minute with code execution
		t.start()

		for s in strats_to_update:
			if(s.indicator1.name not in ['price', 'volume']):
				if(s.indicator1.name == 'number' or force or self.min_count % self.time_map[s.indicator1.interval]  ==  0):
					self.strat_data[s.pk]['indicator1'] = s.indicator1.evaluate(kite_fetcher = self.kf, instrument = int(s.instrument))

			if(s.indicator2.name not in ['price', 'volume']):
				if(s.indicator2.name == 'number' or force or self.min_count % self.time_map[s.indicator2.interval]  ==  0):
					self.strat_data[s.pk]['indicator2'] = s.indicator2.evaluate(kite_fetcher = self.kf, instrument = int(s.instrument))		
		self.min_count += 1


	def strategy_status(self, s):
		if(s.indicator1.name in ['price', 'volume']):
			self.strat_data[s.pk]['indicator1'] = self.global_data[int(s.instrument)][s.indicator1.name]
		indicator1 = self.strat_data[s.pk]['indicator1']

		if(s.indicator2.name in ['price', 'volume']):
			self.strat_data[s.pk]['indicator2'] = self.global_data[int(s.instrument)][s.indicator2.name]
		indicator2 = self.strat_data[s.pk]['indicator2']

		prev = self.strat_data[s.pk]['status']
		ret = False

		c = int(s.comparator)
		if(c == 1):		#greater than
			if(indicator1 > indicator2):
				ret = True

		elif(c == 2):	#less than
			if(indicator1 < indicator2):
				ret = True

		elif(c == 3):	#crosses above
			if(prev==False and  indicator1 > indicator2):
				ret = True

		elif(c == 4):	#crosses below
			if(prev==False and  indicator1 < indicator2):
				ret = True
		
		if(prev == True):
			return ret, self.strat_data[s.pk]['timestamp']
		else:
			return ret, pd.Timestamp('today')



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
			
			# if(not self.time_stamp == pd.Timestamp('today').minute):
			# 	for k in self.global_data.keys():
			# 		self.global_data[k]['open'] = self.global_data[k]['price']
			# 		self.global_data[k]['high'] = 0
			# 		self.global_data[k]['low'] = 999999
			# 		self.time_stamp = pd.Timestamp('today').minute

			for i in ticks:		
				t = i['instrument_token']
				self.global_data[t]['price'] = i['last_price']
				self.global_data[t]['volume'] = i['volume']				

				# if(self.global_data[t]['high'] < i['last_price']):
				# 	self.global_data[t]['high'] = i['last_price']

				# if(self.global_data[t]['low'] > i['last_price']):
				# 	self.global_data[t]['low'] = i['last_price']



			strategy_meta = dict()
			for s in self.strat_list:
				t = int(s.instrument)

				self.strat_data[s.pk]['status'] ,self.strat_data[s.pk]['timestamp'] = self.strategy_status(s)

				strategy_meta[str(s)] = {
					'status' : str(self.strat_data[s.pk]['status']),
					'timestamp' : self.strat_data[s.pk]['timestamp'],
					# 'price' : str(np.round(self.global_data[t]['price'], 4)),
					# 'volume' : str(np.round(self.global_data[t]['volume']) ),
					'price' : str(self.global_data[t]['price']),
					'volume' : str(self.global_data[t]['volume']) ,
					'indicator 1' : str(self.strat_data[s.pk]['indicator1']) + "<br>"+ str(s.indicator1) +"" ,
					'indicator 2' : str(self.strat_data[s.pk]['indicator2']) + "<br>"+ str(s.indicator2) +"" 
				}


			df = pd.DataFrame(strategy_meta)
			new_columns = df.columns[(df.ix['timestamp'] ).argsort()]
			df = df[new_columns[::-1]]
			strategy_meta = df.to_dict()

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