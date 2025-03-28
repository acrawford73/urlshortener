from django.conf import settings

from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.views import View

from .models import News

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class NewsListView(ListView):
	model = News
	template_name = 'news/news_list.html'
	context_object_name = 'news'
	ordering = ['-created']

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'News'
		return context