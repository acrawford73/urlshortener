from django.urls import path, re_path
from . import views


urlpatterns = [

	path('', views.ShortenerListView.as_view()),
	
	path('create/', views.ShortenerCreateView.as_view(), name='shortener-create'),
	path('mylinks/', views.ShortenerListView.as_view(), name='my-links-list'),
	path('toplinks/', views.ShortenerTopListView.as_view(), name='top-links-list'),

	path('shorten/', views.shorten_url, name='shorten-url'),
	path('<str:alias>/', views.redirect_url, name='redirect-url'),

]