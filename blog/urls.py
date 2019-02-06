from django.urls import path
from . import views


urlpatterns = [
    path('', views.clist, name='clist'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('company/<int:pk>/', views.clist_detail, name='clist_detail'),
    path('company/<int:pk>/submit', views.createstrategy, name='createstrategy'),
]