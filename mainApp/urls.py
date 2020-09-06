from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('machines/', views.machines, name='machines'),
    path('worker/<str:pk>/', views.worker, name="worker"),

    path('create_task/<str:pk>/', views.createTask, name="create_task"),
    #path('create_worker/', views.createWorker, name="create_worker"),
    path('update_task/<str:pk>/', views.updateTask, name="update_task"),
    path('delete_task/<str:pk>/', views.deleteTask, name="delete_task"),

]
