from django.urls import path
from . import views


urlpatterns = [

	path('', views.ShortenerListView.as_view(), name='all'),
	
	path('create/', views.ShortenerCreateView.as_view(), name='shortener-create'),
	path('update/<int:pk>/', views.ShortenerUpdateView.as_view(), name='shortener-update'),
	path('short/<int:pk>/', views.ShortenerDetailView.as_view(), name='shortener-detail'),
	path('mylinks/', views.ShortenerListView.as_view(), name='my-links-list'),
	path('toplinks/', views.ShortenerTopListView.as_view(), name='top-links-list'),

	path('shorten/', views.shorten_url, name='shorten-url'),
	path('<str:alias>/', views.redirect_url, name='redirect-url'),

]