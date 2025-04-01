from django.urls import path
import uuid
from . import views


urlpatterns = [

	# Public without login
	path('',						views.ShortenerListViewOpen.as_view(), 		name='shortener-list-open'),
	path('share/tag/<slug:tag_slug>/',	views.ShortenerListByTagViewOpen.as_view(), name='shortener-list-by-tag-open'),

	# Login only
	path('my_links/',				views.ShortenerListView.as_view(), 			name='shortener-list'),
	path('all_links/',				views.ShortenerAllListView.as_view(), 		name='shortener-list-all'),
	
	path('my_links/top/', 			views.ShortenerTopListView.as_view(), 		name='shortener-list-top'),
	path('all_links/top/',		 	views.ShortenerTopAllListView.as_view(), 	name='shortener-list-top-all'),
	
	path('create/', 				views.ShortenerCreateView.as_view(), 		name='shortener-create'),
	path('update/<uuid:pk>/', 		views.ShortenerUpdateView.as_view(), 		name='shortener-update'),
	path('update/all/<uuid:pk>/', 	views.ShortenerAllUpdateView.as_view(), 	name='shortener-update-all'),
	path('detail/<uuid:pk>/', 		views.ShortenerDetailView.as_view(), 		name='shortener-detail'),
	path('detail/all/<uuid:pk>/', 	views.ShortenerAllDetailView.as_view(), 	name='shortener-detail-all'),
	path('delete/<uuid:pk>/',		views.ShortenerDeleteView.as_view(), 		name='shortener-delete'),
	path('delete/all/<uuid:pk>/',		views.ShortenerAllDeleteView.as_view(), 	name='shortener-delete-all'),
	path('my_links/user/<uuid:pk>/',	views.ShortenerByOwnerListView.as_view(),	name='shortener-list-owner'),
	path('all_links/user/<uuid:pk>/',	views.ShortenerAllByOwnerListView.as_view(),	name='shortener-list-owner-all'),

	path('tags/download/', 			views.tags_download, 						name='tags-download'),
	path('tags/suggestions/', 		views.tags_suggestions, 					name='tags-suggestions'),
	path('tags/<slug:tag_slug>/', 	views.ShortenerListByTagView.as_view(), 	name='shortener-list-by-tag'),
	path('tags/all/<slug:tag_slug>/', 	views.ShortenerAllListByTagView.as_view(), 	name='shortener-list-by-tag-all'),
	path('topics/',					views.TagsListView.as_view(),				name='tags-list'),

	#path('tags/autocomplete/', 	views.TagAutocompleteView.as_view(), name='tags_autocomplete'),

	# keep this last
	path('<str:alias>/', 			views.redirect_url, 						name='redirect-url'),

]