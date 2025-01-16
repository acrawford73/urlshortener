from django.urls import path, re_path
from . import views

urlpatterns = [

	path('terms/', views.Terms.as_view(), name='terms'),
	path('privacy/', views.Help.as_view(), name='privacy'),
	path('help/', views.Help.as_view(), name='help'),
	path('license/', views.Help.as_view(), name='license'),

]
