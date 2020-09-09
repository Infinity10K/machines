from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('machines/', views.machines, name='machines'),
    path('worker/<str:pk>/', views.worker, name="worker"),

    path('create_task/<str:pk>/', views.createTask, name="create_task"),
    path('create_task_machine/<str:pk>/', views.createTaskMachine, name="create_task_machine"),
    #path('create_worker/', views.createWorker, name="create_worker"),
    path('update_task/<str:pk>/', views.updateTask, name="update_task"),
    path('delete_task/<str:pk>/', views.deleteTask, name="delete_task"),
    path('machine/<str:pk>/', views.machineInfo, name="machine_info"),

]
