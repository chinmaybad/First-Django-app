from django.shortcuts import render
from .models import Post
from .models import Strategy
from .models import Companies
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from celery.result import AsyncResult
from .tasks import do_work
from django.http import HttpResponse
import json
import logging
logger = logging.getLogger(__name__)


# Create your views here.
def post_list(request):
	posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
	return render(request, 'blog/post_lists.html', {'posts': posts})
def post_detail(request, pk):
	post = get_object_or_404(Post, pk=pk)
	return render(request, 'blog/post_detail.html', {'post': post})

def clist(request):
	companies = Companies.objects.all()
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

			task_obj = do_work.apply_async([s.pk])
			strat.task_id = task_obj.id
			strat.save()

			companies = Companies.objects.all()                

			return render(request, "blog/nav.html",{'companies': companies})
	else:
		companies = Companies.objects.all()
		return render(request, "blog/nav.html",{'companies': companies})  


def display_dashboard(request):    
	# strat_list = Strategy.objects.all()
	# task_id = ''

	# for s in strat_list:
	# 	print('\n\nFor '+ str(s))

	# result = AsyncResult(s.task_id)
	# state = result.state
	# print('original state : '+state)

	# if(not str(state) == 'PROGRESS'):
	# print('passing instrument as parameter : '+ str(s))
	# task_obj = do_work.apply_async(args=[s.instrument] , kwargs={'kwarg1':'token'})
	# task_obj = do_work.apply_async([s.pk] , expires=30)
	task_obj = do_work.apply_async(expires=45)
	print('Assigned new ID = ' + str(task_obj.id))
	# s.task_id = task_obj.id

	# s.save()

	# print('Data sent to Dashboard.html')
	# for s in strat_list:
	# 	print(str(s) + ' task_id = ' + str(s.task_id))
	return render(request, 'blog/dashboard.html',{"task_id" : task_obj.id})

def get_progress(request, task_id):
	print('get_progress :: task_id :- ' + task_id)
	result = AsyncResult(task_id)
	data = dict()
	try:
		data = {
			'state': result.state,
			'instruments': result.info['instruments'],
			'price': result.info['price'],
			'volume': result.info['volume'],
			'task_id':task_id
			}
		print('\n####Data : ' + str(data))
	except:
		print('Error RESULT \n state = ' + str(result.state) + '\tDetails = '+str(result.info))
		data = {
			'state': 'EXCEPT',
			'instruments' : 12121,
			'price': 111,
			'volume': 99999,
			'task_id':task_id
			}
		pass	
	# logger.warning('Received Task Id :' +str(task_id) + '\t Global task Id : '+str(task_id))
	return HttpResponse(json.dumps(data), content_type='application/json') 

	
			
