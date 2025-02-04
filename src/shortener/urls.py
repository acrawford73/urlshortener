from django.urls import path
import uuid
from . import views


urlpatterns = [

	path('', 					views.ShortenerListView.as_view()),
	
	path('create/', 			views.ShortenerCreateView.as_view(), 	name='shortener-create'),
	path('edit/<uuid:pk>/', 	views.ShortenerUpdateView.as_view(), 	name='shortener-update'),
	path('delete/<uuid:pk>/',	views.ShortenerDeleteView.as_view(), 	name='shortener-delete'),
	path('detail/<uuid:pk>/', 	views.ShortenerDetailView.as_view(), 	name='shortener-detail'),
	path('recent/',				views.ShortenerListView.as_view(), 		name='shortener-list'),
	path('top/', 				views.ShortenerTopListView.as_view(), 	name='shortener-list-top'),

	path('shorten/', 			views.shorten_url, 						name='shorten-url'),
	path('<str:alias>/', 		views.redirect_url, 					name='redirect-url'),

]