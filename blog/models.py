from django.conf import settings
from django.db import models
from django.utils import timezone


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


class Strategy(models.Model):
	name=models.CharField(max_length=100)
	comparator=models.CharField(max_length=100)
	indicator1=models.CharField(max_length=100)
	indicator2=models.CharField(max_length=100)
	instrument=models.CharField(max_length=100)

	task_id = models.CharField(max_length=100, default='')
	alloted = models.DateTimeField(default=timezone.now)


	def __str__(self):
		ind_map = {"price":"Price", "volume":"Volume", "ma_price" : "Moving Avg. (Price)", "ma_volume":"Moving Avg. (Volume)"}
		comp = '  <  '
		if(int(self.comparator) == 1):
			comp = '  > '

		return str(self.name +'('+ self.instrument +') ::  '+
			ind_map[self.indicator1] + comp + ind_map[self.indicator2])


class Refreshed(models.Model):
	name = models.CharField(max_length=100)
	status = models.CharField(max_length=100, default = 'False')