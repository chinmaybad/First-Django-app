from kiteconnect import KiteConnect
import pandas as pd
import numpy as np
import datetime


class KiteFetcher(object):

	def __init__(self, access_token):
		self.kite = KiteConnect(api_key="0ld4qxtvnif715ls")
		self.kite.set_access_token(access_token)		

	def get_passed_indicators(self, token, indi_list):
		values = dict()
		if('ma_price' in indi_list  and  'ma_volume' in indi_list):
			indi_list.remove('ma_volume')

		for i in  indi_list:
			if(i == 'ma_price'):
				MA = self.getMovingAverage(token)
				# print('MA = ' +str(MA))
				values.update(MA)

			if(i == 'ma_volume'):
				MA = self.getMovingAverage(token)
				# print('MA = ' +str(MA))
				values.update(MA)

		return values
				


	def getMovingAverage(self, instrument, days=20):
		to_date = pd.Timestamp('today').round('min')
		from_date = to_date.round('d')+ pd.Timedelta(days = -1*days, hours=9.25)

		data = self.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval='minute', continuous=0)    
		df =  pd.DataFrame(data)
		return {'ma_price' : np.round(np.mean(df['close']), 2), 'ma_volume' : np.round(np.mean(df['volume']), 2) }	