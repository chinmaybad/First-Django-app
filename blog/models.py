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
	PMO_type = list()

	def __init__(self):
		 self.interval = ['minute', 'day', '3minute','5minute','10minute','15minute','30minute','60minute']
		 self.ma_type=["price","volume"]
		 self.kd_type = ["% K", "% D"]
		 self.slowk_matype = ['SMA', 'EMA', 'Double', 'Triple', 'Triangular']
		 self.slowd_matype = ['SMA', 'EMA', 'Double', 'Triple', 'Triangular']
		 self.band_type = ['upper', 'middle', 'lower']
		 self.field = ["close", "open", "high", "low"]
		 self.PMO_type = ['PMO', 'PMO_signal']



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

class Standard_Deviation(Indicator):	
	period = models.CharField(max_length=100, default='10')
	interval = models.CharField(max_length=100, default='minute')
	field = models.CharField(max_length=100, default='close')
# · minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

		return np.std(df[field][-1 * period : ], 4)

	def __str__(self):
		return "std( "+ self.period +", "+ self.interval +", "+ self.field +")"
		# return "Moving Avg. | "+ self.ma_type +" >> "+ self.period +" x "+ self.interval

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



class RSI(Indicator):
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
		df['MFM'] = (2*df.loc[:, 'close'] - df.loc[:, 'high'] - df.loc[:, 'low']) / (df.loc[:, 'high'] - df.loc[:, 'low'])
		df['MFV'] = df.loc[:, 'MFM'] * df.loc[:, 'volume']		
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
		
		df['HL'] = df['high'] - df['low']
		HL_EMA = talib.EMA ( df['HL'] , timeperiod=int(self.period))
		result =  (HL_EMA.iloc[-1] / HL_EMA.iloc[-1*(int(self.rate_of_change)+1)]  - 1) * 100
		return np.round(result , 4)

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
		return "MACD-signal("+ self.fastperiod +", "+ self.slowperiod +", "+ self.signalperiod +", "+ self.interval +")"


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
		return "MACD-histogram("+ self.fastperiod +", "+ self.slowperiod +", "+ self.signalperiod +", "+ self.interval +")"	



class Parabolic_SAR(Indicator):	#Moving Average Convergence/Divergence Histogram
	acceleration = models.CharField(max_length=100, default='0.02')
	maximum = models.CharField(max_length=100, default='0.2')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)
		result = talib.SAR(high=df['high'], low=df['low'], acceleration=float(self.acceleration), maximum=float(self.maximum))
		return np.round(result.iloc[-1], 2)

	def __str__(self):
		return "P-SAR("+ self.acceleration +", "+ self.maximum +", "+ self.interval +")"


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
		
		atr = 'ATR'
		st, stx = 'supertrend', 'stx'
		df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=period)
			# Compute basic upper and lower bands
		df['basic_ub'] = (df.loc[:, 'high']+ df.loc[:, 'low']) / 2 + multiplier * df[atr]
		df['basic_lb'] = (df.loc[:, 'high']+ df.loc[:, 'low']) / 2 - multiplier * df[atr]

		# Compute final upper and lower bands
		df['final_ub'] = 0.00
		df['final_lb'] = 0.00
		for i in range(period, len(df)):
			df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or df['close'].iat[i - 1] > df['final_ub'].iat[i - 1] else df['final_ub'].iat[i - 1]
			df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or df['close'].iat[i - 1] < df['final_lb'].iat[i - 1] else df['final_lb'].iat[i - 1]
		   
		# Set the Supertrend value
		df[st] = 0.00
		for i in range(period, len(df)):
			df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[i] <= df['final_ub'].iat[i] else \
							df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[i] >  df['final_ub'].iat[i] else \
							df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] >= df['final_lb'].iat[i] else \
							df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] <  df['final_lb'].iat[i] else 0.00 
				 
	# Mark the trend direction up/down
		df[stx] = np.where((df[st] > 0.00), np.where((df['close'] < df[st]), 'down',  'up'), np.NaN)

	# Remove basic and final bands from the columns
		df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)
	
		df.fillna(0, inplace=True)

		return np.round(df['supertrend'].iloc[-1], 2)

	def __str__(self):
		return "Supertrend("+ self.interval +", "+ self.period +", " + self.multiplier +")"	



class Bollinger_Band(Indicator):	#Moving Average Convergence/Divergence Histogram
	period = models.CharField(max_length=100, default='14')
	std = models.CharField(max_length=100, default='2')
	field = models.CharField(max_length=100, default='close')
	interval = models.CharField(max_length=100, default='minute')	
	band_type = models.CharField(max_length=100, default='middle')	

	def evaluate(self, kite_fetcher, instrument):
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)
		close_col = self.field
		d = int(self.std)
		period = int(self.period)
		df['bol_bands_middle'] = df[close_col].ewm(ignore_na=False, min_periods=0, com=period, adjust=True).mean()

		index = df.index[-1]
		s = df[close_col].iloc[index - period: index]		
		middle_band = df.at[index, 'bol_bands_middle']
		if(self.band_type == 'middle'):
			return np.round(middle_band, 2)

		sums = 0
		for e in s:
			sums += np.square(e - middle_band)

		std = np.sqrt(sums / period)
		if(self.band_type == 'upper'):
			return np.round(middle_band + (d * std), 2)
		else:
			return np.round(middle_band - (d * std), 2)

	def __str__(self):
		return "BBAND(" + self.band_type +", "+ self.period +", "+ self.interval +", "+ self.std + ")"


class Money_Flow_Index(Indicator):	
	period = models.CharField(max_length=100, default='10')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.MFI(high = df['high'], low = df['low'], close = df['close'], volume = df['volume'], timeperiod = period)
		return np.round(result, 4)

	def __str__(self):
		return "MFI( "+ self.period +", "+ self.interval +")"

class VWAP(Indicator):	
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		to_date = pd.Timestamp('today')
		from_date = pd.Timestamp(to_date.date())

		data = kite_fetcher.kite.historical_data(instrument_token = instrument, from_date = from_date , to_date = to_date, interval=self.interval, continuous=0)
		df =  pd.DataFrame(data)

		df['mean'] = (df.loc[: , 'low'] + df[:, 'high'] + df[:, 'close']) /3
		df['mul'] = df[:, 'mean'] * df[:, 'volume']
		try:
			result = np.sum(df.loc[:, 'mul']) / np.sum(df.loc[:, 'vol'])
		except:
			result = 0
		return np.round(result, 4)

	def __str__(self):
		return "VWAP( "+ self.interval +")"


class ATR(Indicator):	
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.TRANGE(high = df['high'], low = df['low'], close = df['close'])
		return np.round(result, 4)

	def __str__(self):
		return "True Range( "+ self.interval +")"


class ATR(Indicator):	
	period = models.CharField(max_length=100, default='10')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.ATR(high = df['high'], low = df['low'], close = df['close'], timeperiod = period)
		return np.round(result, 4)

	def __str__(self):
		return "ATR( "+ self.period +", "+ self.interval +")"

class Momentum_Indicator(Indicator):	
	period = models.CharField(max_length=100, default='14')
	interval = models.CharField(max_length=100, default='minute')	

	def evaluate(self, kite_fetcher, instrument):
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)

		result = talib.MOM(close = df['close'], timeperiod = period)
		return np.round(result, 4)

	def __str__(self):
		return "Momentum( "+ self.period +", "+ self.interval +")"


class High_Low(Indicator):	
	interval = models.CharField(max_length=100, default='minute')
	
	def evaluate(self, kite_fetcher, instrument):
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)
		# print('\n\nhigh = ' + str(df['high'].iloc[-1]))
		# print('\n\nlow = ' + str(df['low'].iloc[-1]))
		result = df['high'].iloc[-1] - df['low'].iloc[-1]
		return np.round(result, 4)

	def __str__(self):
		return "High - Low( "+ self.interval +")"

class Price_Momentum_Oscillator(Indicator):	
	field = models.CharField(max_length=100, default='close')
	interval = models.CharField(max_length=100, default='minute')	
	smoothing_period = models.CharField(max_length=100, default='35')	
	double_smoothing_period = models.CharField(max_length=100, default='20')	
	signal_period = models.CharField(max_length=100, default='10')	
	PMO_type = models.CharField(max_length=100, default='PMO')	
	

	def evaluate(self, kite_fetcher, instrument):
	# https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:dppmo
		s_period = int(self.smoothing_period)
		ds_period =int(self.double_smoothing_period)
		sig = int(self.signal_period)
		df = self.get_large_data(kite_fetcher=kite_fetcher, instrument=instrument)

		df['ROC'] = df[self.field].pct_change() * 100
		mul_35 = float(2)/s_period
		mul_20= float(2)/ds_period
		df['35-EMA'] = 0
		df['20-EMA'] = 0

		df.loc[s_period+1, '35-EMA'] = np.mean(df.loc[1:s_period, 'ROC'])

		for i in range(s_period+2, len(df)):
			df.loc[i, '35-EMA'] = df.loc[i, 'ROC'] * mul_35  +  df.loc[i-1, '35-EMA'] * (1-mul_35)

		df.loc[:, '35-EMA'] = df.loc[:, '35-EMA'] * sig
		df.loc[s_period + ds_period + 1, '20-EMA'] = np.mean(df.loc[s_period+2 : s_period+ds_period+1, '35-EMA'])    

		for i in range(s_period + ds_period + 2, len(df)):
			df.loc[i, '20-EMA'] = (df.loc[i, '35-EMA'] -  df.loc[i-1, '20-EMA'] ) * mul_20  +  df.loc[i-1, '20-EMA']

		if(self.PMO_type == 'PMO_signal'):
			df['signal']  = talib.EMA(df.loc[:, '20-EMA'], timeperiod=sig)
			return np.round(df['signal'].iloc[-1], 4)
		else:
			return np.round(df['20-EMA'].iloc[-1], 4)

	def __str__(self):
		return "PMO( "+ self.smoothing_period +", "+ self.double_smoothing_period +", "+ self.signal_period +", "+ self.interval +")"


class Intraday_Momentum_Index(Indicator):
	period = models.CharField(max_length=100, default='20')
	interval = models.CharField(max_length=100, default='minute')

	def evaluate(self, kite_fetcher, instrument):
		# https://library.tradingtechnologies.com/trade/chrt-ti-intraday-momentum-index.html
		period = int(self.period)
		df = self.get_small_data(kite_fetcher=kite_fetcher, instrument=instrument)
		df = df.iloc[-1*period: , :]
		diff = df.loc[:, 'close'] - df.loc[:, 'open']
		up = diff[diff > 0]
		down = diff[diff < 0]

		try:
			sUp, sDown = np.sum(up), abs(np.sum(down))
			result = (sUp / (sUp + sDown)) * 100
		except:
			result = 0
		return np.round(result, 3)

	def __str__(self):
		return "IMI("+ self.period +", "+ self.interval +")"


class Strategy(models.Model):
	name=models.CharField(max_length=100)
	comparator=models.CharField(max_length=100)
	indicator1 = models.OneToOneField(Indicator, on_delete=models.CASCADE, related_name = 'indicator1', null=True)
	indicator2 = models.OneToOneField(Indicator, on_delete=models.CASCADE, related_name = 'indicator2', null=True)
	instrument=models.CharField(max_length=100)

	def __str__(self):
		return self.name +'('+ self.instrument +')'

	def cond_str(self):
		comp_dict = {'1' : ' > ', '2' :' < ', '3':' Crosses Above ', '4':' Crosses Below '}
		return str(self.indicator1) + comp_dict[self.comparator] + str(self.indicator2)


class Strategy_Group(models.Model):
	name=models.CharField(max_length=100)
	exp=models.CharField(max_length=200, default = 'True')
	display=models.CharField(max_length=200, default = 'NONE')

	def __str__(self):
		return self.name

	def cond_str(self):
		return self.exp