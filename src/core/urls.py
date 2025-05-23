from django.urls import path
from . import views

urlpatterns = [

	path('terms/', views.Terms.as_view(), name='terms'),
	path('privacy/', views.Privacy.as_view(), name='privacy'),
	path('help/', views.Help.as_view(), name='help'),
	path('license/', views.License.as_view(), name='license'),
	path('guidelines/', views.Guidelines.as_view(), name='guidelines'),
	path('faq/', views.FAQ.as_view(), name='faq'),

	# Robots
	path('robots.txt', views.Robots.as_view(content_type='text/plain'), name='robots'),

	# Security
	path('.well-known/security.txt', views.Security.as_view(content_type='text/plain'), name='security'),

]
