from django.shortcuts import render, redirect
from .models import Post
from .models import Strategy, Companies, Refreshed, Indicator, Choices
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from celery.result import AsyncResult
from .tasks import do_work
from django.http import HttpResponse
import json
import logging
import pandas as pd
import os
from django.apps import apps

logger = logging.getLogger(__name__)


def post_list(request):
	posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
	return render(request, 'blog/post_lists.html', {'posts': posts})
def post_detail(request, pk):
	post = get_object_or_404(Post, pk=pk)
	return render(request, 'blog/post_detail.html', {'post': post})

def clist(request):
	companies = Companies.objects.all()

	print('reading csv in NAV | clist')
	path = os.getcwd() + '/blog/extras/task.csv'
	df = pd.read_csv(path, index_col=False)		
	task_id = str(df['task_id'][0])

	result = AsyncResult(task_id)
	print('State = ' + str(result.state))

	if(not result.state == "PROGRESS"):
		task_obj = do_work.apply_async()
		task_id = task_obj.id
		print('Assigned new ID = ' + str(task_id))


	indilist=Indicator.__subclasses__()   
	indicatorl=list()
	for a in indilist:
		a=str(a).split(".")[2]
		a=a.split("\'")[0]
		indicatorl.append(a) 

	return render(request, 'blog/nav.html', {'companies': companies,"indicatorlist":indicatorl})

def clist_detail(request,pk):
	companies = Companies.objects.all()
	comp = get_object_or_404(Companies,pk=pk)
	indilist=Indicator.__subclasses__()   
	indicatorl=list()
	for a in indilist:
		a=str(a).split(".")[2]
		a=a.split("\'")[0]
		indicatorl.append(a) 

	return render(request, 'blog/nav.html', {'companies': companies,'comp':comp,"indicatorlist":indicatorl})


def updatestrategy(request,pk):
	if request.method == 'POST':
		sid=request.POST.get('strat')
		strat = get_object_or_404(Strategy,pk=sid)
		strat.indicator1 = strat.indicator1.down_cast()
		strat.indicator2 = strat.indicator2.down_cast()

		companies = Companies.objects.all()
		# len1=int(request.POST.get('for1'))
		# len2=int(request.POST.get('for2'))
		
		indi1=apps.get_model("blog",str(strat.indicator1.__class__.__name__))()

		indi2=apps.get_model("blog",str(strat.indicator2.__class__.__name__))()
		print(strat.id)

		fullfieldlist=indi1._meta.get_fields(include_parents=False)
		shortfieldlist=list()
		i=0
		print(str(fullfieldlist))

		for a in fullfieldlist:
			if i==0:
				pass
			else:
				
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				shortfieldlist.append(a)
			i+=1
	   
		c=True


		for a in shortfieldlist:
			if not request.POST.get(str(a)+"1"):
				c=False

		fullfieldlist2=indi2._meta.get_fields(include_parents=False)
		shortfieldlist2=list()
		print("----------------------------------------")
		i=0

		for a in fullfieldlist2:
			if i==0:
				pass
			else:
			   
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				shortfieldlist2.append(a)
			i+=1
	  

		for a in shortfieldlist2:
			if not request.POST.get(str(a)+"2"):
				c=False



		if c:
			for a in shortfieldlist:

			   setattr(strat.indicator1,a,request.POST.get(str(a)+"1"))
			   print(getattr(strat.indicator1,a))
			   print("set inside")

			for a in shortfieldlist2:
			   setattr(strat.indicator2,a,request.POST.get(str(a)+"2"))
			   print(getattr(strat.indicator2,a))
		
		strat.indicator1.save() 
		strat.indicator2.save()
		strat.save()


		print(strat.id)


		s = Strategy.objects.all().filter(pk = strat.id)
		s = list(s)[0]
		print('Strategy created = '+str(s))
		print('Indicator1 = '+str(s.indicator1.down_cast()))
		print('Indicator2 = '+str(s.indicator2.down_cast()))
		print("done!!!!!!!!")

		return render(request, "blog/nav.html",{'companies': companies})  




def createstrategy(request,pk):
	if request.method == 'POST':
		if request.POST.get('indicator1') and request.POST.get('indicator2') and request.POST.get('comparator') and request.POST.get('name') and request.POST.get('instrument') :
			strat=Strategy()
			
			strat.comparator= request.POST.get('comparator')
			strat.name= request.POST.get('name')
			strat.instrument= request.POST.get('instrument')
			i1=apps.get_model("blog",request.POST.get('indicator1'))()
			i1.save()


			i2=apps.get_model("blog",request.POST.get('indicator2'))()
			i2.save()
			strat.indicator1=i1 
			strat.indicator2=i2


		   
			strat.task_id = "task_obj.id"
			strat.save()
			print(strat.id)
		  
			sq=strat.indicator1._meta.get_fields(include_parents=False)
			print("SQ is ----------"+str(sq))
			sp=list()

			for a in sq:
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				sp.append(a)





			sq2=strat.indicator2._meta.get_fields(include_parents=False)
			sp2=list()

			for a in sq2:
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				sp2.append(a)

			# indicator=Indicators.create(request.POST.get('indicator1'))
			# if(request.POST.get('indicator1')=='MovingAverage'):
			#     indicator.indi.create(request.POST.get('period'),request.POST.get('interval'))
			# if(request.POST.get('indicator2')=='MovingAverage'):
			#     indicator.indi.create(request.POST.get('period'),request.POST.get('interval'))

			# indicator.save()

			companies = Companies.objects.all()  
			indilist=Indicator.__subclasses__() 
			indicatorl=list()
			for a in indilist:
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				indicatorl.append(a)
			choice=Choices()             

			r = Refreshed(name="Strategy")
			r.save()
			print("\nAdded refresh object")
			return render(request, "blog/nav2.html",{'companies': companies,"strat":strat.id,"fieldlist1":sp,"fieldlist2":sp2,"indicatorlist":indicatorl,"choice":choice})
	else:
		companies = Companies.objects.all()
		return render(request, "blog/nav.html",{'companies': companies})  


def display_dashboard(request):    	

	strat_list = Strategy.objects.all()

	print('reading csv')
	path = os.getcwd() + '/blog/extras/task.csv'
	df = pd.read_csv(path, index_col=False)		
	task_id = str(df['task_id'][0])

	result = AsyncResult(task_id)
	print('State = ' + str(result.state))

	if(not result.state == "PROGRESS"):
		task_obj = do_work.apply_async()
		task_id = task_obj.id
		print('Assigned new ID = ' + str(task_id))


	return render(request, 'blog/dashboard.html',{"task_id" : task_id, "strat_list" : strat_list})



def revoke(request,task_id):
	strat_list = Strategy.objects.all()
	task_obj = do_work.apply_async()

	path = os.getcwd() + '/blog/extras/task.csv'
	df = pd.read_csv(path, index_col=False)		
	df['task_id'] = task_obj.id
	df.to_csv(path, index=False)

	return redirect('/dashboard',{"task_id":task_obj.id,"strat_list":strat_list})



def get_progress(request, task_id):
	print('get_progress :: task_id :- ' + task_id)
	result = AsyncResult(task_id)
	data = dict()
	try:
		# data = {
		# 	'state': result.state,
		# 	'meta' : result.info
		# 	}
		data = result.info
		# print('\n####Data : ' + str(data))
	except:
		# print('Error RESULT \n state = ' + str(result.state) + '\tDetails = '+str(result.info))
		print('EXCEPT')
		pass	

	return HttpResponse(json.dumps(data), content_type='application/json') 

	
			


def manage(request):
	strat_list = Strategy.objects.all()
	return render(request, 'blog/manage.html',{"strat_list":strat_list})

def strat_detail(request,pk):
	strat_list = Strategy.objects.all()
	strat = get_object_or_404(Strategy,pk=pk)

	strat.indicator1.delete()
	strat.indicator2.delete()
	strat.delete()
	
	r = Refreshed(name="Strategy")
	r.save()
	print("\nAdded refresh object")
	return redirect('manage')