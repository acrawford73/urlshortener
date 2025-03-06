from django.urls import path
import uuid
from . import views


urlpatterns = [

	path('recent/',					views.ShortenerListView.as_view(), 		name='shortener-list'),
	path('top/', 					views.ShortenerTopListView.as_view(), 	name='shortener-list-top'),
	path('create/', 				views.ShortenerCreateView.as_view(), 	name='shortener-create'),
	path('update/<uuid:pk>/', 		views.ShortenerUpdateView.as_view(), 	name='shortener-update'),
	path('delete/<uuid:pk>/',		views.ShortenerDeleteView.as_view(), 	name='shortener-delete'),
	path('detail/<uuid:pk>/', 		views.ShortenerDetailView.as_view(), 	name='shortener-detail'),
	path('detail/exists/<uuid:pk>/', views.ShortenerDetailExistsView.as_view(), name='shortener-detail-exists'),
	path('recent/user/<int:pk>/',	 views.ShortenerListByOwnerView.as_view(), 	name='shortener-list-owner'),

	path('tags/download/', 			views.tags_download, 					name='tags-download'),
	path('tags/suggestions/', 		views.tags_suggestions, 				name='tags-suggestions'),
	path('tags/<slug:tag_slug>/', 	views.ShortenerListByTagView.as_view(), name='shortener-list-by-tag'),
	path('tags/',					views.TagsListView.as_view(),			name='tags-list'),

	#path('tags/autocomplete/', 	views.TagAutocompleteView.as_view(), name='tags_autocomplete'),

	# keep this last
	path('<str:alias>/', 			views.redirect_url, 					name='redirect-url'),

]