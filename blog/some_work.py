import time
import logging
logger = logging.getLogger(__name__)
import logging
from kiteconnect import KiteTicker
from time import sleep
import pandas as pd
import datetime
from celery.task.control import revoke
from threading import Timer
from django.shortcuts import get_object_or_404
from .models import Strategy
from .indicators import KiteFetcher

class Work(object):

	def __init__(self, task):
		strat_list = Strategy.objects.all()
		self.task = task
		self.tokens = list()		

		for s in strat_list:
			self.tokens.append(int(s.instrument))

		kf = KiteFetcher()
		MA = dict()
		for t in self.tokens:
			try:
				MA[t] = kf.getMovingAverage(t)
			except:
				print('Error in calculating MA : '+str(t))
				pass


	def run(self):      
		tokens = self.tokens
		print('Tokens ='+str(tokens))
		time.sleep()
		kws = KiteTicker('0ld4qxtvnif715ls', 'Owdx20eaGn8HgaYY67peFNE8g4ZypeeQ')
		
		hmap = dict()
		for i, t in enumerate(tokens):
			hmap[t]	 = i
		price = [0]*len(tokens)
		volume = [0]*len(tokens)

		def on_ticks(ws, ticks):
		
			for i in ticks:		
				index = hmap[i['instrument_token']]
				price[index] = i['last_price']
				volume[index] = i['volume']

			temp = {
					'state' : 'PROGRESS',
					'instruments' : tokens,
					'price' : price,
					'volume' : volume,
					'task_id' : self.task.request.id
				}
			self.task.update_state(state='PROGRESS', meta=temp)
			print(str(temp))	
						  

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

		def stop_gracefully():
			kws.stop_retry()
			kws.close()
			print('____________________Closed KiteTicker Gracefully_________________')

		kws.on_ticks = on_ticks
		kws.on_close = on_close
		kws.on_error = on_error
		kws.on_connect = on_connect
		kws.on_reconnect = on_reconnect
		kws.on_noreconnect = on_noreconnect

		timer = Timer(30, stop_gracefully)
		timer.start()
		kws.connect(threaded=False)