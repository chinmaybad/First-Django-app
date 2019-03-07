from django.urls import path,re_path
from . import views


urlpatterns = [
    path('', views.clist, name='clist'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('company/<int:pk>/', views.clist_detail, name='clist_detail'),
    path('company/<int:pk>/next', views.createstrategy, name='createstrategy'),
    path('company/<int:pk>/submit', views.updatestrategy, name='updatestrategy'),
    path('dashboard', views.display_dashboard, name='dashboard'),
    path('manage', views.manage, name='manage'),
    path('manage/<int:pk>/', views.strat_detail, name='strat_detail'),
    path('delete_all', views.delete_all, name='delete_all'),
    re_path(r'(?P<task_id>[\w-]*)/revoke', views.revoke, name='revoke'),    
    re_path(r'(?P<task_id>[\w-]*)/', views.get_progress, name='get_progress'),
]