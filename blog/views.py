from django.shortcuts import render, redirect
from .models import Post
from .models import Strategy, Companies, Refreshed
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from celery.result import AsyncResult
from .tasks import do_work
from django.http import HttpResponse
import json
import logging
import pandas as pd
import os

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

	return render(request, 'blog/nav.html', {'companies': companies})

def clist_detail(request,pk):
	companies = Companies.objects.all()
	comp = get_object_or_404(Companies,pk=pk)
	return render(request, 'blog/nav.html', {'companies': companies,'comp':comp})

def createstrategy(request,pk):
	if request.method == 'POST':
		if request.POST.get('indicator1') and request.POST.get('indicator2') and request.POST.get('comparator') and request.POST.get('name') and request.POST.get('instrument') :
			strat=Strategy()
			strat.indicator1= request.POST.get('indicator1')
			strat.indicator2= request.POST.get('indicator2')
			strat.comparator= request.POST.get('comparator')
			strat.name= request.POST.get('name')
			strat.instrument= request.POST.get('instrument')

			strat.save()

			companies = Companies.objects.all()      

			r = Refreshed(name="Strategy")
			r.save()
			print("\nAdded refresh object")
			return render(request, "blog/nav.html",{'companies': companies})
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
	strat.delete()
	r = Refreshed(name="Strategy")
	r.save()
	print("\nAdded refresh object")
	return redirect('manage')