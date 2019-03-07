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


class Choices():
	interval=list()
	ma_type=list()
	kd_type = list()
	slowk_matype = list()
	slowd_matype = list()
	band_type = list()
	field = list()

	def __init__(self):
		 self.interval = ['minute', 'day', '3minute','5minute','10minute','15minute','30minute','60minute']
		 self.ma_type=["price","volume"]
		 self.kd_type = ["% K", "% D"]
		 self.slowk_matype = ['SMA', 'EMA', 'Double', 'Triple', 'Triangular']
		 self.slowd_matype = ['SMA', 'EMA', 'Double', 'Triple', 'Triangular']
		 self.band_type = ['upper', 'middle', 'lower']
		 self.field = ["close", "open", "high", "low"]



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
		day_dict = dict({'minute' : 7, 'day':250, '3minute':10, '5minute':12, '10minute':15,'15minute':20,'30minute':30,'60minute':60})
		to_date = pd.Timestamp('today')
		from_date = to_date.round('d')


		from_date += pd.Timedelta(days = -1 * day_dict[self.interval])
		data = kite_fetcher.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval=self.interval, continuous=0)
		df =  pd.DataFrame(data)
		return df
	
	def get_small_data(self, kite_fetcher, instrument):
		df = None
		day_dict = dict({'minute' : 4, 'day':100, '3minute':6, '5minute':7, '10minute':10,'15minute':12,'30minute':15,'60minute':30})
		to_date = pd.Timestamp('today')
		from_date = to_date.round('d')


		from_date += pd.Timedelta(days = -1 * day_dict[self.interval])
		data = kite_fetcher.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval=self.interval, continuous=0)
		df =  pd.DataFrame(data)
		return df

	# def get_filled_data(self, self, kite_fetcher, instrument):
	# 	df = get_small_data(kite_fetcher = kite_fetcher, instrument = instrument)



class Price(Indicator):
	pass

class Volume(Indicator):
	pass

#A dummy class for comparision of RSI,etc with a given value
class Number(Indicator):
	value = models.CharField(max_length=100, default='50')
	
	def __str__(self):
		return self.value

	def evaluate(self, kite_fetcher, instrument):
		return float(self.value)

class Moving_Average(Indicator):	
	ma_type = models.CharField(max_length=100, default='price')		#price or volume
	period = models.CharField(max_length=100, default='10')
	interval = models.CharField(max_length=100, default='minute')	
# · minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

		if(self.ma_type == 'price'):
			return np.round(np.mean(df['close'][-1 * period : ]), 2)
		else:
			return np.round(np.mean(df['volume'][-1 * period : ]))

	def __str__(self):
		return "MA( "+ self.ma_type +", "  + self.period +", "+ self.interval +")"
		# return "Moving Avg. | "+ self.ma_type +" >> "+ self.period +" x "+ self.interval


# EMA = (closing price - previous day's EMA) × smoothing constant as a decimal + previous day's EMA
# "previous day's EMA" for first calculation will be the SMA(Simple MA) calc. for old data

class Exponential_Moving_Average(Indicator):	#EMA
	ma_type = models.CharField(max_length=100, default='price')		#price or volume
	period = models.CharField(max_length=100, default='20')
	interval = models.CharField(max_length=100, default='minute')	

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
		return "EMA( "+ self.ma_type +", "  + self.period +", "+ self.interval +")"



class RSI(Indicator):		#inaccurate for DAY
	period = models.CharField(max_length=100, default='14')
	interval = models.CharField(max_length=100, default='minute')
	# prev_val = models.CharField(max_length=100, default='0')

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

# RSI = 100 – [100 / ( 1 + (Average of Upward Price Change / Average of Downward Price Change ) ) ]		
		rsi = talib.RSI(df['close'], timeperiod=period)
		return np.round(rsi.iloc[-2], 2)

	def __str__(self):
		return "RSI("+ self.period +", "+ self.interval +")"


class ADX(Indicator):	#Average Directional Movement
	period = models.CharField(max_length=100, default='20')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.ADX(high=df['high'], close=df['close'], low=df['low'], timeperiod=period)
		return np.round(result.iloc[-1] , 2)

	def __str__(self):
		return "ADX("+ self.period +", "+ self.interval +")"	


class Aroon_Oscillator(Indicator):	#Uptrend or Downtrend
	period = models.CharField(max_length=100, default='25')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.AROONOSC(high=df['high'], low=df['low'].values, timeperiod=period)
		return np.round(result.iloc[-1] , 2)

	def __str__(self):
		return "Aroon_Oscillator("+ self.period +", "+ self.interval +")"	



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
		df['MFM'] = (2*df['close'] - df['high'] - df['low']) / (df['high'] - df['low'])
		df['MFV'] = df['MFM'] * df['volume']		
		CMF = np.sum(df['MFV'])/np.sum(df['volume'])		
		return np.round(CMF , 4)

	def __str__(self):
		return "CMF("+ self.period +", "+ self.interval +")"	



class Chaikin_Volatility(Indicator):	#compares the spread between a security's high and low prices
#MAJOR ERROR
	period = models.CharField(max_length=100, default='10')
	rate_of_change = models.CharField(max_length=100, default='2')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)
# Volatility = [(High Low Average - High Low Average n Periods ago) / High Low Average n Periods ago] * 100
# First, calculate an exponential moving average (normally 10 days) of the difference between High and Low for each period: EMA [H-L]
# Next, calculate the percentage change in the moving average over a further period (normally 10 days):
# ( EMA [H-L] - EMA [H-L 10 days ago] ) / EMA [ H-L 10 days ago] * 100
		
		# df['HL'] = df['high'] - df['low']
		# HL_EMA = talib.EMA ( df['HL'] , timeperiod=period)
		# result =  (HL_EMA.iloc[-1] / HL_EMA.iloc[-1*(period+1)]  - 1) * 100
		# return np.round(result , 4)
		import blog.extra_indicators as extras 
		result = extras.chaikin_volatility(df, ema_periods=int(self.period), change_periods=int(self.rate_of_change), high_col='high', low_col='low', close_col='close')
		return np.round(result['chaikin_volatility'].iloc[-1] , 4)

	def __str__(self):
		return "CV("+ self.period +", "+ self.rate_of_change +", "+ self.interval +")"			


# class Chaikin_Oscillator(Indicator):	#compares the spread between a security's high and low prices
# 	period = models.CharField(max_length=100, default='10')
# 	rate_of_change = models.CharField(max_length=100, default='2')
# 	interval = models.CharField(max_length=100, default='minute')	

# 	def evaluate(self, kite_fetcher, instrument):
# 		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)
# 		df.columns = ['Close', 'Date', 'High', 'Low', 'Open', 'Volume']
# 		ad = (2 * df['Close'] - df['High'] - df['Low']) / (df['High'] - df['Low']) * df['Volume']  
# 		Chaikin = pd.Series(pd.ewma(ad, span = 3, min_periods = 2) - pd.ewma(ad, span = 10, min_periods = 9), name = 'Chaikin')  
# 		# df = df.join(Chaikin)  
# 		return Chaikin.iloc[-1]




class MACD(Indicator):	#Moving Average Convergence/Divergence		MINOR ERRORS
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
		return "MACD("+ self.fastperiod +", "+ self.slowperiod +", "+ self.signalperiod +", "+ self.interval +")"


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
		return "MACD("+ self.fastperiod +", "+ self.slowperiod +", "+ self.signalperiod +", "+ self.interval +")"


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
		return "MACD("+ self.fastperiod +", "+ self.slowperiod +", "+ self.signalperiod +", "+ self.interval +")"	



class Parabolic_SAR(Indicator):	#Moving Average Convergence/Divergence Histogram
	acceleration = models.CharField(max_length=100, default='0.02')
	maximum = models.CharField(max_length=100, default='0.2')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)
		result = talib.SAR(high=df['high'], low=df['low'], acceleration=float(self.acceleration), maximum=float(self.maximum))
		return np.round(result.iloc[-1], 2)

	def __str__(self):
		return "MACD("+ self.acceleration +", "+ self.maximum +", "+ self.interval +")"


#help(talib.MA_Type)
# SMA  : SMA = 0
# EMA  : EMA = 1
# Weighted  :  WMA = 2
# Triple  :  TEMA = 4
# Triangular  :  TRIMA = 5
# Double  :  DEMA = 3
# Hull : NA

class Stochastic(Indicator):	#Moving Average Convergence/Divergence Histogram
	interval = models.CharField(max_length=100, default='minute')
	kd_type = models.CharField(max_length=100, default='%K')		# %K or %D
	fastk_period = models.CharField(max_length=100, default='10')
	slowk_period = models.CharField(max_length=100, default='3')
	slowk_matype = models.CharField(max_length=100, default='EMA')
	slowd_period = models.CharField(max_length=100, default='10')
	slowd_matype = models.CharField(max_length=100, default='EMA')
	

	def evaluate(self, kite_fetcher, instrument):
		TMA = talib.MA_Type
		MA_dict = {'SMA' : TMA.SMA, 'EMA' : TMA.EMA, 'Double' : TMA.DEMA, 'Triple' : TMA.TEMA, 'Triangular' : TMA.TRIMA}

		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		slowk, slowd = talib.STOCH( df['high'], df['low'], df['close'], fastk_period=int(self.fastk_period), slowk_period=int(self.slowk_period),
		slowk_matype=MA_dict[self.slowk_matype], slowd_period=int(self.slowd_period), slowd_matype=MA_dict[self.slowd_matype] )

		if(self.kd_type == "% K"):
			return np.round(slowk.iloc[-1], 2)
		else:
			return np.round(slowd.iloc[-1], 2)

	def __str__(self):
		return "Stochastic("+self.interval + ", "+self.kd_type +")"	


class Supertrend(Indicator):	#Moving Average Convergence/Divergence Histogram
	interval = models.CharField(max_length=100, default='10minute')
	period = models.CharField(max_length=100, default='7')		# %K or %D
	multiplier = models.CharField(max_length=100, default='3')
	

	def evaluate(self, kite_fetcher, instrument):	
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)
		period = int(self.period)
		multiplier = int(self.multiplier)

# http://www.freebsensetips.com/blog/detail/7/What-is-supertrend-indicator-its-calculation
# BASIC UPPERBAND  =  (HIGH + LOW) / 2 + Multiplier * ATR
# BASIC LOWERBAND =  (HIGH + LOW) / 2 - Multiplier * ATR

# FINAL UPPERBAND = IF( (Current BASICUPPERBAND  < Previous FINAL UPPERBAND) and (Previous Close > Previous FINAL UPPERBAND))
# 	THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)

# FINAL LOWERBAND = IF( (Current BASIC LOWERBAND  > Previous FINAL LOWERBAND) and (Previous Close < Previous FINAL LOWERBAND))
# 	THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)

# SUPERTREND = IF(Current Close <= Current FINAL UPPERBAND )
# 	THEN Current FINAL UPPERBAND
# 	ELSE Current  FINAL LOWERBAND

		df.columns = ['Close', 'Date', 'High', 'Low', 'Open', 'Volume']
		#df is the dataframe, n is the period, f is the factor; f=3, n=7 are commonly used.
		f, n = multiplier, period    
		df['H-L']=abs(df['High']-df['Low'])
		df['H-PC']=abs(df['High']-df['Close'].shift(1))
		df['L-PC']=abs(df['Low']-df['Close'].shift(1))
		df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1)
		df['ATR']=np.nan
		df.ix[n-1,'ATR']=df['TR'][:n-1].mean() #.ix is deprecated from pandas verion- 0.19
		for i in range(n,len(df)):
			df['ATR'][i]=(df['ATR'][i-1]*(n-1)+ df['TR'][i])/n

		#Calculation of SuperTrend
		df['Upper Basic']=(df['High']+df['Low'])/2+(f*df['ATR'])
		df['Lower Basic']=(df['High']+df['Low'])/2-(f*df['ATR'])
		df['Upper Band']=df['Upper Basic']
		df['Lower Band']=df['Lower Basic']
		for i in range(n,len(df)):
			if df['Close'][i-1]<=df['Upper Band'][i-1]:
				df['Upper Band'][i]=min(df['Upper Basic'][i],df['Upper Band'][i-1])
			else:
				df['Upper Band'][i]=df['Upper Basic'][i]    
		for i in range(n,len(df)):
			if df['Close'][i-1]>=df['Lower Band'][i-1]:
				df['Lower Band'][i]=max(df['Lower Basic'][i],df['Lower Band'][i-1])
			else:
				df['Lower Band'][i]=df['Lower Basic'][i]   
		df['SuperTrend']=np.nan
		for i in df['SuperTrend']:
			if df['Close'][n-1]<=df['Upper Band'][n-1]:
				df['SuperTrend'][n-1]=df['Upper Band'][n-1]
			elif df['Close'][n-1]>df['Upper Band'][i]:
				df['SuperTrend'][n-1]=df['Lower Band'][n-1]
		for i in range(n,len(df)):
			if df['SuperTrend'][i-1]==df['Upper Band'][i-1] and df['Close'][i]<=df['Upper Band'][i]:
				df['SuperTrend'][i]=df['Upper Band'][i]
			elif  df['SuperTrend'][i-1]==df['Upper Band'][i-1] and df['Close'][i]>=df['Upper Band'][i]:
				df['SuperTrend'][i]=df['Lower Band'][i]
			elif df['SuperTrend'][i-1]==df['Lower Band'][i-1] and df['Close'][i]>=df['Lower Band'][i]:
				df['SuperTrend'][i]=df['Lower Band'][i]
			elif df['SuperTrend'][i-1]==df['Lower Band'][i-1] and df['Close'][i]<=df['Lower Band'][i]:
				df['SuperTrend'][i]=df['Upper Band'][i]

		return np.round(df['SuperTrend'].iloc[-1], 2)	

	def __str__(self):
		return "Supertrend("+ self.interval +", "+ self.period +", " + self.multiplier +")"	



class Bollinger_Band(Indicator):	#Moving Average Convergence/Divergence Histogram
	period = models.CharField(max_length=100, default='14')
	standard_deviation = models.CharField(max_length=100, default='2')
	field = models.CharField(max_length=100, default='close')
	interval = models.CharField(max_length=100, default='minute')	
	band_type = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)
		close_col = self.field
		d = int(self.standard_deviation)
		period = int(self.period)
		df['bol_bands_middle'] = df[close_col].ewm(ignore_na=False, min_periods=0, com=period, adjust=True).mean()

		index = df.index[-1]
		s = df[close_col].iloc[index - period: index]		
		middle_band = df.at[index, 'bol_bands_middle']
		if(self.band_type == 'middle'):
			return middle_band

		sums = 0
		for e in s:
			sums += np.square(e - middle_band)

		std = np.sqrt(sums / period)
		if(self.band_type == 'upper'):
			return middle_band + (d * std)
		else:
			return middle_band - (d * std)

	def __str__(self):
		return "BBAND(" + self.band_type +", "+ self.period +", "+ self.interval +")"


class Strategy(models.Model):
	name=models.CharField(max_length=100)
	comparator=models.CharField(max_length=100)
	indicator1 = models.OneToOneField(Indicator, on_delete=models.CASCADE, related_name = 'indicator1', null=True)
	indicator2 = models.OneToOneField(Indicator, on_delete=models.CASCADE, related_name = 'indicator2', null=True)
	instrument=models.CharField(max_length=100)

	def __str__(self):
		comp_dict = {'1' : ' > ', '2' :' < ', '3':' Crosses Above ', '4':' Crosses Below '}
		return self.name +'('+ self.instrument +') ::  '+str(self.indicator1) + comp_dict[self.comparator] + str(self.indicator2)
