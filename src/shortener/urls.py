from django.urls import path
from . import views


urlpatterns = [

	path('create/', views.ShortenerCreateView.as_view(), name='shortener-create'),
	path('my-links/', views.ShortenerListView.as_view(), name='shortener-list'),
	path('top-links/', views.ShortenerTopListView.as_view(), name='top-list'),

	path('shorten/', views.shorten_url, name='shorten-url'),
	path('<str:alias>/', views.redirect_url, name='redirect-url'),

]