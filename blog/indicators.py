from kiteconnect import KiteConnect
import pandas as pd
import numpy as np
import datetime


class KiteFetcher(object):

	def __init__(self):
		self.kite = KiteConnect(api_key="0ld4qxtvnif715ls")
		self.kite.set_access_token('Owdx20eaGn8HgaYY67peFNE8g4ZypeeQ')		

	def getMovingAverage(self, instrument, days=20):
	    to_date = pd.Timestamp('today').round('min')
	    from_date = to_date.round('d')+ pd.Timedelta(days = -20, hours=9.25)
	    data = kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval='minute', continuous=0)    
	    df =  pd.DataFrame(data)
	    return dict('ma_price' : np.mean(df['close']), 'ma_volume' : np.mean(df['volume'])



