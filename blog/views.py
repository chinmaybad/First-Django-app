
from django.shortcuts import render, redirect
from .models import Post
from .models import Strategy, Companies, Refreshed, Indicator, Choices,Strategy_Group
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
import blog.extras.access_token as AT
from django.db.models import Q

logger = logging.getLogger(__name__)




# Global Variables
Instrument_List=list()
Strategy_Ids=list() #Used in Nav and StratGroup
Strategy_String=str()
Strategy_String_Display=str()


def post_list(request):
	posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
	return render(request, 'blog/post_lists.html', {'posts': posts})
def post_detail(request, pk):
	post = get_object_or_404(Post, pk=pk)
	return render(request, 'blog/post_detail.html', {'post': post})

def clist(request):
	Companies_List = Companies.objects.all()

	task_id = AT.get_task_id()

	result = AsyncResult(task_id)
	print('State = ' + str(result.state))

	if(not result.state == "PROGRESS"):
		task_obj = do_work.apply_async()
		task_id = task_obj.id
		print('Assigned new ID = ' + str(task_id))


	indilist=Indicator.__subclasses__()   
	Indicators_List=list()
	for a in indilist:
		a=str(a).split(".")[2]
		a=a.split("\'")[0]
		Indicators_List.append(a) 

	return render(request, 'blog/nav.html', {'companies': Companies_List,"indicatorlist":Indicators_List})

def clist_detail(request,pk):
	global Instrument_List


	Companies_List = Companies.objects.all()
	comp = get_object_or_404(Companies,pk=pk)
	Instrument_List.append(comp.token)
	indilist=Indicator.__subclasses__()   
	Indicators_List=list()
	for a in indilist:
		a=str(a).split(".")[2]
		a=a.split("\'")[0]
		Indicators_List.append(a) 

	return render(request, 'blog/nav.html', {'companies': Companies_List,'comp':comp,"indicatorlist":Indicators_List,"instrumentlist":str(Instrument_List)})


def clear(request):

	print("clear called")
	Companies_List = Companies.objects.all()

	global Instrument_List
	Instrument_List.clear()
	indilist=Indicator.__subclasses__()   
	Indicators_List=list()
	for a in indilist:
		a=str(a).split(".")[2]
		a=a.split("\'")[0]
		Indicators_List.append(a) 


	print("clear called")

	return render(request, 'blog/nav.html', {'companies': Companies_List,"indicatorlist":Indicators_List})



def updatestrategy(request,pk):
	if request.method == 'POST':

		global Strategy_Ids
		for ids in Strategy_Ids:
			sid=ids
			strat = get_object_or_404(Strategy,pk=sid)
			strat.indicator1 = strat.indicator1.down_cast()
			strat.indicator2 = strat.indicator2.down_cast()

			Companies_List = Companies.objects.all()
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

		Strategy_Ids.clear()
		r = Refreshed(name="Strategy")
		r.save()
		print("\nAdded refresh object")

		return render(request, "blog/nav.html",{'companies': Companies_List})  




def createstrategy(request,pk):
	if request.method == 'POST':
		if request.POST.get('indicator1') and request.POST.get('indicator2') and request.POST.get('comparator') and request.POST.get('name') and request.POST.get('instrument') :

			global Instrument_List
			global Strategy_Ids
			for instruments in Instrument_List:
				strat=Strategy()             
				strat.comparator= request.POST.get('comparator')
				strat.name= request.POST.get('name')
				strat.instrument= instruments
				i1=apps.get_model("blog",request.POST.get('indicator1'))()
				i1.save()
				i2=apps.get_model("blog",request.POST.get('indicator2'))()
				i2.save()
				strat.indicator1=i1 
				strat.indicator2=i2
				strat.task_id = "task_obj.id"
				strat.save()
				print(strat.id)
				Strategy_Ids.append(strat.id)
		  
			Indicator1_Fields=strat.indicator1._meta.get_fields(include_parents=False)
		
			# Indicator1_Fields_List=list()
			Indicator1_Fields_Dict=dict()
			Indicator2_Fields_Dict=dict()

			for a in Indicator1_Fields:
				t=a
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				# Indicator1_Fields_List.append(a)
				Indicator1_Fields_Dict[a]=t.default





			Indicator2_Fields=strat.indicator2._meta.get_fields(include_parents=False)
			sp2=list()

			for a in Indicator2_Fields:
				t=a
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				# sp2.append(a)
				Indicator2_Fields_Dict[a]=t.default

			# indicator=Indicators.create(request.POST.get('indicator1'))
			# if(request.POST.get('indicator1')=='MovingAverage'):
			#     indicator.indi.create(request.POST.get('period'),request.POST.get('interval'))
			# if(request.POST.get('indicator2')=='MovingAverage'):
			#     indicator.indi.create(request.POST.get('period'),request.POST.get('interval'))

			# indicator.save()

			Companies_List= Companies.objects.all()  
			indilist=Indicator.__subclasses__() 
			Indicators_List=list()
			for a in indilist:
				a=str(a).split(".")[2]
				a=a.split("\'")[0]
				Indicators_List.append(a)
			choice=Choices()   
			
			Instrument_List.clear()          
			
			return render(request, "blog/nav2.html",{'companies': Companies_List,"strat":strat.id,"fieldlist1":Indicator1_Fields_Dict,"fieldlist2":Indicator2_Fields_Dict,"indicatorlist":Indicators_List,"choice":choice, "strat_obj" : strat})
	else:
		Companies_List = Companies.objects.all()
		return render(request, "blog/nav.html",{'companies': Companies_List})  


def display_dashboard(request):    	

	strat_list = Strategy.objects.all()

	task_id = AT.get_task_id()

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

	AT.set_task_id(task_obj.id)

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
	from django.db.models import Q
	strat_list = Strategy.objects.filter(~Q(name = "DO_NOT_DELETE"))

	strat_group = Strategy_Group.objects.filter(~Q(name = "DO_NOT_DELETE"))

	return render(request, 'blog/manage.html',{"strat_list":strat_list, "strat_group_list":strat_group})

def strat_detail(request,pk):
	strat = get_object_or_404(Strategy,pk=pk)

	strat.indicator1.delete()
	strat.indicator2.delete()
	strat.delete()
	
	r = Refreshed(name="Strategy")
	r.save()
	print("\nAdded refresh object")
	return redirect('manage')

def strat_group_detail(request,pk):
	strat = get_object_or_404(Strategy,pk=pk)
	strat.delete()
	
	r = Refreshed(name="Strategy_Group")
	r.save()
	print("\nAdded refresh object")
	return redirect('manage')


def delete_all(request):	

	for strat in Strategy.objects.filter(~Q(name = "DO_NOT_DELETE")):
		strat.indicator1.delete()
		strat.indicator2.delete()
		strat.delete()

	for strat in Strategy_Group.objects.filter(~Q(name = "DO_NOT_DELETE")):
		strat.delete()

	r = Refreshed(name="Strategy")
	r.save()
	r = Refreshed(name="Strategy_Group")
	r.save()
	print("\nAdded refresh object")
	return redirect('manage')



def stratgroup(request):

	global Strategy_Ids
	Strategy_Ids.clear()

	strat_list = Strategy.objects.filter(~Q(name = "DO_NOT_DELETE"))
	global Strategy_String_Display


	return render(request, 'blog/stratgroup.html',{"strat_list":strat_list,"stratstring":Strategy_String_Display})


def stratselect(request,pk):


	global Strategy_String,Strategy_Ids,Strategy_String_Display

	print("selected")

	strat_list = Strategy.objects.filter(~Q(name = "DO_NOT_DELETE"))
	strat = get_object_or_404(Strategy,pk=pk)
	

	Strategy_String=Strategy_String+str(strat.pk)
	Strategy_String_Display=Strategy_String_Display+" "+str(strat.name)+"("+str(strat.instrument)+")"


	


	return render(request, 'blog/stratgroup.html',{"strat_list":strat_list,"stratstring":Strategy_String_Display})



def stratAnd(request):

	global Strategy_String,Strategy_String_Display

	Strategy_String=Strategy_String+" and "
	Strategy_String_Display=Strategy_String_Display+" and "

	strat_list = Strategy.objects.filter(~Q(name = "DO_NOT_DELETE"))
	


	return render(request, 'blog/stratgroup.html',{"strat_list":strat_list,"stratstring":Strategy_String_Display})


def stratOr(request):

	global Strategy_String,Strategy_String_Display

	Strategy_String=Strategy_String+" or "
	Strategy_String_Display=Strategy_String_Display+" or "

	strat_list = Strategy.objects.filter(~Q(name = "DO_NOT_DELETE"))
	


	return render(request, 'blog/stratgroup.html',{"strat_list":strat_list,"stratstring":Strategy_String_Display})



def stratclear(request):
	global Strategy_String, Strategy_Ids,Strategy_String_Display

	strat_list = Strategy.objects.filter(~Q(name = "DO_NOT_DELETE"))
	Strategy_String=""
	Strategy_String_Display=""
	Strategy_Ids.clear()
	


	return render(request, 'blog/stratgroup.html',{"strat_list":strat_list,"stratstring":Strategy_String})

def stratgroupsubmit(request):

	global Strategy_String,Strategy_String_Display
	Companies_List = Companies.objects.all() 
	print("here")

	if request.method == 'POST':

		group=Strategy_Group()
		group.name=request.POST.get('groupname')
		group.exp=Strategy_String
		group.display = Strategy_String_Display
		print(Strategy_String)
		group.save()

		print("Group created with "+ group.name+"   "+group.exp)

		r = Refreshed(name="Strategy_Group")
		r.save()


		Strategy_String=""
		Strategy_String_Display=""

	return render(request, "blog/nav.html",{'companies': Companies_List})  













