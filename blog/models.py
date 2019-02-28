from django.conf import settings
from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from model_utils.managers import InheritanceManager
import talib


class Post(models.Model):
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	title = models.CharField(max_length=200)
	text = models.TextField()
	created_date = models.DateTimeField(default=timezone.now)
	published_date = models.DateTimeField(blank=True, null=True,default=timezone.now)

	def publish(self):
		self.published_date = timezone.now()
		self.save()

	def __str__(self):
		return self.title


class Companies(models.Model):
	name = models.CharField(max_length=100)
	token = models.CharField(max_length=100)
	fullname = models.CharField(max_length=100,default='')

	def publish(self):
		self.save()

	def __str__(self):
		return 'Company name: '+self.name+' Company Token: '+self.token+' Company Full name: '+self.fullname



class Refreshed(models.Model):
	name = models.CharField(max_length=100)
	status = models.CharField(max_length=100, default = 'False')


class Indicator(models.Model):
	name = models.CharField(max_length=100, default='')
	objects = InheritanceManager()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# print("super init called")
		if(self.name == ''):
			self.name = self.__class__.__name__.lower()
		# print(self.name)

	def __str__(self):
		return str(self.name)

	def evaluate(self):
		return 0

	def down_cast(self, kite_fetcher=None, instrument=None):
		s = Indicator.objects.select_subclasses(self.name).filter(pk=self.pk)
		if(len(s) > 0):
			return s[0]
		return self

	def get_large_data(self, kite_fetcher, instrument):
		df = None
		interval = self.interval
		to_date = pd.Timestamp('today').round('min')
		from_date = to_date.round('d')

		if(interval == 'day'):
			from_date += pd.Timedelta(days = -100)
			data = kite_fetcher.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval=interval, continuous=0)
			df =  pd.DataFrame(data)
		else:
			from_date += pd.Timedelta(days = -30)
			data = kite_fetcher.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval=interval, continuous=0)
			df =  pd.DataFrame(data)
		return df
	
	def get_small_data(self, kite_fetcher, instrument):
		df = None
		interval = self.interval
		to_date = pd.Timestamp('today').round('min')
		from_date = to_date.round('d')

		if(interval == 'day'):
			from_date += pd.Timedelta(days = -50)
			data = kite_fetcher.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval=interval, continuous=0)
			df =  pd.DataFrame(data)
		else:
			from_date += pd.Timedelta(days = -15)
			data = kite_fetcher.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval=interval, continuous=0)
			df =  pd.DataFrame(data)
		return data


class Price(Indicator):
	pass

class Volume(Indicator):
	pass

#A dummy class for comparision of RSI,etc with a given value
class Number(Indicator):
	value = models.CharField(max_length=100, default='50')	
	
	def __str__(self):
		return self.N

	def evaluate(self, kite_fetcher, instrument):
		return float(self.N)

class Moving_Average(Indicator):	
	ma_type = models.CharField(max_length=100, default='price')		#price or volume
	period = models.CharField(max_length=100, default='20')
	interval = models.CharField(max_length=100, default='minute')	
# · minute
# · day
# · 3minute
# · 5minute
# · 10minute
# · 15minute
# · 30minute
# · 60minute

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

		if(self.ma_type == 'price'):
			return np.mean(df['close'][-1 * period : ])
		else:
			return np.mean(df['volume'][-1 * period : ])

	def __str__(self):
		return "MA | "+ self.ma_type +  + self.period +" x "+ self.interval
		# return "Moving Avg. | "+ self.ma_type +" >> "+ self.period +" x "+ self.interval


# EMA = (closing price - previous day's EMA) × smoothing constant as a decimal + previous day's EMA
# "previous day's EMA" for first calculation will be the SMA(Simple MA) calc. for old data

class Exponential_Moving_Average(Indicator):	#EMA
	ma_type = models.CharField(max_length=100, default='price')		#price or volume
	period = models.CharField(max_length=100, default='20')
	interval = models.CharField(max_length=100, default='minute')	
	# prev_val = models.CharField(max_length=100, default='0')
	# last_updated = models.DateTimeField(blank=True, null=True,default=timezone.now)

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		if(self.ma_type == 'price'):
			data = df['close']
		else:
			data = df['volume']

		# long_rolling = data.rolling(window=period).mean()
		# ema_short = data.ewm(span=20, adjust=False).mean()
		result = talib.EMA(data, timeperiod=period)
		return np.round(result.iloc[-1] , 2)

	def __str__(self):
		return "EMA | "+ self.ma_type +  + self.period +" x "+ self.interval



class RSI(Indicator):	
	period = models.CharField(max_length=100, default='14')
	interval = models.CharField(max_length=100, default='minute')
	# prev_val = models.CharField(max_length=100, default='0')

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

# RSI = 100 – [100 / ( 1 + (Average of Upward Price Change / Average of Downward Price Change ) ) ]		
		delta = df['close'][-1 * (period+1) : ].diff()		#eg. 15 candles for period of 14 to calc. detla
		up = delta[delta > 0]
		down = delta[delta<0]
		rs = np.mean(up) / np.mean(down)

		return np.round(100 -  100/(1+rs), 2)

	def __str__(self):
		return "RSI | "+ self.period +" x "+ self.interval


class ADX(Indicator):	#Average Directional Movement
	period = models.CharField(max_length=100, default='20')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.ADX(high=df['high'], close=df['close'], low=df['low'], timeperiod=period)
		return np.round(result.iloc[-1] , 2)

	def __str__(self):
		return "ADX | " +self.period +" x "+ self.interval		


class Aroon_Oscillator(Indicator):	#Uptrend or Downtrend
	period = models.CharField(max_length=100, default='25')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.AROONOSC(high=df['high'], low=df['low'].values, timeperiod=period)
		return np.round(result.iloc[-1] , 2)

	def __str__(self):
		return "ADX | " +self.period +" x "+ self.interval



class Chaikin_Money_Flow(Indicator):	#Uptrend or Downtrend
	period = models.CharField(max_length=100, default='25')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

# Money Flow Multiplier = [(Close  -  Low) - (High - Close)] /(High - Low) 
# Money Flow Volume = Money Flow Multiplier x Volume for the Period
# 20-period CMF = 20-period Sum of Money Flow Volume / 20 period Sum of Volume
		df = df.iloc[-period:]
		df['MFM'] = 2*df['close'] - df['high'] - df['low']
		df['MFV'] = df['MFM'] * df['volume']		
		CMF = np.sum(df['MFV'])/np.sum(df['volume'])		
		return np.round(CMF , 4)

	def __str__(self):
		return "CMF | " +self.period +" x "+ self.interval



class Chaikin_Volatility(Indicator):	#compares the spread between a security's high and low prices
	period = models.CharField(max_length=100, default='10')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

# Volatility = [(High Low Average - High Low Average n Periods ago) / High Low Average n Periods ago] * 100
# First, calculate an exponential moving average (normally 10 days) of the difference between High and Low for each period: EMA [H-L]
# Next, calculate the percentage change in the moving average over a further period (normally 10 days):
# ( EMA [H-L] - EMA [H-L 10 days ago] ) / EMA [ H-L 10 days ago] * 100
		
		df['HL'] = df['high'] - df['low']
		HL_EMA = talib.EMA ( df['HL'] , timeperiod=period)
		result =  (HL_EMA.iloc[-1] / HL_EMA.iloc[-1*(period+1)]  - 1) * 100
		return np.round(result , 4)

	def __str__(self):
		return "CV | " +self.period +" x "+ self.interval


class MACD(Indicator):	#Moving Average Convergence/Divergence
	fastperiod = models.CharField(max_length=100, default='12')
	slowperiod = models.CharField(max_length=100, default='26')
	signalperiod = models.CharField(max_length=100, default='9')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		macd, macdsignal, macdhist = talib.MACD(df['close'], fastperiod=int(self.fastperiod), slowperiod=int(self.slowperiod),
			signalperiod=int(self.signalperiod))
		return np.round(macd.iloc[-1] , 4)

	def __str__(self):
		return "MACD"


class MACD_Signal(Indicator):	#Moving Average Convergence/Divergence Signal
	fastperiod = models.CharField(max_length=100, default='12')
	slowperiod = models.CharField(max_length=100, default='26')
	signalperiod = models.CharField(max_length=100, default='9')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		macd, macdsignal, macdhist = talib.MACD(df['close'], fastperiod=int(self.fastperiod), slowperiod=int(self.slowperiod),
			signalperiod=int(self.signalperiod))
		return np.round(macdsignal.iloc[-1], 4)

	def __str__(self):
		return "MACD-signal"


class MACD_Histogram(Indicator):	#Moving Average Convergence/Divergence Histogram
	fastperiod = models.CharField(max_length=100, default='12')
	slowperiod = models.CharField(max_length=100, default='26')
	signalperiod = models.CharField(max_length=100, default='9')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		macd, macdsignal, macdhist = talib.MACD(df['close'], fastperiod=int(self.fastperiod), slowperiod=int(self.slowperiod),
			signalperiod=int(self.signalperiod))
		return np.round(macdhist.iloc[-1], 4)

	def __str__(self):
		return "MACD-histogram"		



class Parabolic_SAR(Indicator):	#Moving Average Convergence/Divergence Histogram
	acceleration = models.CharField(max_length=100, default='0.02')
	maximum = models.CharField(max_length=100, default='0.2')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_samll_data(kite_fetcher=kite_fetcher, instrument=instrument)
		result = talib.SAR(high=df['high'], low=df['low'], acceleration=int(self.acceleration), maximum=int(self.maximum))
		return np.round(result.iloc[-1], 2)

	def __str__(self):
		return "Parabolic SAR"


#help(talib.MA_Type)
# SMA  : SMA = 0
# EMA  : EMA = 1
# Weighted  :  WMA = 2
# Triple  :  TEMA = 4
# Triangular  :  TRIMA = 5
# Double  :  DEMA = 3
# Hull

class Stochastic(Indicator):	#Moving Average Convergence/Divergence Histogram
	interval = models.CharField(max_length=100, default='minute')
	fastk_period = models.CharField(max_length=100, default='10')
	slowk_period = models.CharField(max_length=100, default='3')
	slowk_matype = models.CharField(max_length=100, default='0.02')
	slowd_period = models.CharField(max_length=100, default='0.02')
	slowd_matype = models.CharField(max_length=100, default='0.02')
	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_samll_data(kite_fetcher=kite_fetcher, instrument=instrument)
		result = talib.SAR(high=df['high'], low=df['low'], acceleration=int(self.acceleration), maximum=int(self.maximum))
		return np.round(result.iloc[-1], 2)

	def __str__(self):
		return "Parabolic SAR"


slowk, slowd = STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)

class Strategy(models.Model):
	name=models.CharField(max_length=100)
	comparator=models.CharField(max_length=100)
	indicator1 = models.OneToOneField(Indicator, on_delete=models.CASCADE, related_name = 'indicator1', null=True)
	indicator2 = models.OneToOneField(Indicator, on_delete=models.CASCADE, related_name = 'indicator2', null=True)
	instrument=models.CharField(max_length=100)

	def __str__(self):
		comp = '  <  '
		if(int(self.comparator) == 1):
			comp = '  > '

		return self.name +'('+ self.instrument +') ::  '+str(self.indicator1) + comp + str(self.indicator2)



