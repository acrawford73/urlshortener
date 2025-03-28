from django.urls import path
import uuid
from . import views


urlpatterns = [

	path('news/', views.NewsListView.as_view(), name='news-list'),

]