from django.urls import path
from . import views


urlpatterns = [

	path('', 					views.ShortenerListView.as_view(), 		name='all'),
	
	path('create/', 			views.ShortenerCreateView.as_view(), 	name='shortener-create'),
	path('edit/<int:pk>/', 		views.ShortenerUpdateView.as_view(), 	name='shortener-update'),
	path('delete/<int:pk>/',	views.ShortenerDeleteView.as_view(), 	name='shortener-delete'),
	path('short/<int:pk>/', 	views.ShortenerDetailView.as_view(), 	name='shortener-detail'),
	path('links/', 				views.ShortenerListView.as_view(), 		name='shortener-list'),
	path('top/', 				views.ShortenerTopListView.as_view(), 	name='top-shortener-list'),

	path('shorten/', 			views.shorten_url, 						name='shorten-url'),
	path('<str:alias>/', 		views.redirect_url, 					name='redirect-url'),

]