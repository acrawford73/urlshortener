from django.urls import path
import uuid
from . import views


urlpatterns = [

	path('recent/',				views.ShortenerListView.as_view(), 		name='shortener-list'),
	path('top/', 				views.ShortenerTopListView.as_view(), 	name='shortener-list-top'),
	path('create/', 			views.ShortenerCreateView.as_view(), 	name='shortener-create'),
	path('edit/<uuid:pk>/', 	views.ShortenerUpdateView.as_view(), 	name='shortener-update'),
	path('delete/<uuid:pk>/',	views.ShortenerDeleteView.as_view(), 	name='shortener-delete'),
	path('detail/<uuid:pk>/', 	views.ShortenerDetailView.as_view(), 	name='shortener-detail'),
	path('<str:alias>/', 		views.redirect_url, 					name='redirect-url'),
	path('tags/<slug:tag_slug>/', views.ShortenerListByTagView.as_view(), name='shortener-list-by-tag'),
	path('tags/autocomplete/', 	views.tags_autocomplete, 				name='tags_autocomplete'),
	#path('tags/autocomplete/', 	views.TagAutocompleteView.as_view(), name='tags_autocomplete'),

]