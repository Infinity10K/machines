from django.shortcuts import render, redirect 
from django.http import HttpResponse
from django.forms import inlineformset_factory
# Create your views here.
from .models import *
from .forms import TaskForm



def home(request):
	tasks = Task.objects.all()
	workers = Worker.objects.all()

	total_workerss = workers.count()

	total_tasks = tasks.count()
	done = tasks.filter(status='Выполнено').count()
	running = tasks.filter(status='Выполняется').count()

	context = {'tasks':tasks, 'workers':workers,
	'total_tasks':total_tasks,'done':done,
	'running':running }

	return render(request, 'mainApp/dashboard.html', context)

def machines(request):
	machines = Machine.objects.all()

	return render(request, 'mainApp/machines.html', {'machines':machines})

def worker(request, pk_test):
	worker = Worker.objects.get(id=pk_test)

	tasks = worker.task_set.all()
	task_count = tasks.count()

	context = {'worker':worker, 'tasks':tasks, 'task_count':task_count}
	return render(request, 'mainApp/worker.html',context)


def createTask(request, pk):
	TaskFormSet = inlineformset_factory(Worker, Task, fields=('machine', 'status'), extra=10 )
	worker = Worker.objects.get(id=pk)
	formset = TaskFormSet(queryset=Task.objects.none(),instance=worker)
	#form = TaskForm(initial={'worker':worker})
	if request.method == 'POST':
		#print('Printing POST:', request.POST)
		#form = TaskForm(request.POST)
		formset = TaskFormSet(request.POST, instance=worker)
		if formset.is_valid():
			formset.save()
			return redirect('/')

	context = {'form':formset}
	return render(request, 'mainApp/task_form.html', context)

def updateTask(request, pk):

	task = Task.objects.get(id=pk)
	form = TaskForm(instance=task)

	if request.method == 'POST':
		form = TaskForm(request.POST, instance=task)
		if form.is_valid():
			form.save()
			return redirect('/')

	context = {'form':form}
	return render(request, 'mainApp/task_form.html', context)

def deleteTask(request, pk):
	task = Task.objects.get(id=pk)
	if request.method == "POST":
		Task.delete()
		return redirect('/')

	context = {'item':task}
	return render(request, 'mainApp/delete.html', context)

#def createWorker(request):
#
#	return redirect('/')
