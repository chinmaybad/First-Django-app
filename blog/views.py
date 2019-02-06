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

                strat.save()
                companies = Companies.objects.all()
                

                return render(request, "blog/nav.html",{'companies': companies})
        else:
            companies = Companies.objects.all()
            return render(request, "blog/nav.html",{'companies': companies})  
def display_dashboard(request):    
        task_obj = do_work.apply_async()
        gloabl_task_id = task_obj.id
    # do_work.delay()
        logger.warning('ID = '+str(gloabl_task_id))
        return render(request, 'blog/dashboard.html',{"task_id":task_obj.id})

def start_work(request):
     # the .delay() call here is all that's needed
     # to convert the function to be called asynchronously     
     # we can't say 'work done' here anymore because all we did was kick it off     
        return HttpResponse('work kicked off!')

def get_progress(request, task_id):
        logger.warning('task_id : ' + task_id)
        result = AsyncResult(task_id)
        data = {'state': result.state,'details': result.info,'task_id':task_id}
        logger.warning('Data : ' + str(data))
        logger.warning('Received Task Id :' +str(task_id) + '\t Global task Id : '+str(task_id))
        return HttpResponse(json.dumps(data), content_type='application/json') 

    
        	
