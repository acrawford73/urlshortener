from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


@method_decorator(cache_page(60*60), name='dispatch')
class Terms(TemplateView):
	template_name = 'core/terms.html'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Terms'
		return context


@method_decorator(cache_page(60*60), name='dispatch')
class Privacy(TemplateView):
	template_name = 'core/privacy.html'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Privacy'
		return context


@method_decorator(cache_page(60*60), name='dispatch')
class License(TemplateView):
	template_name = 'core/license.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'License'
		return context


@method_decorator(cache_page(60*60), name='dispatch')
class Help(LoginRequiredMixin, TemplateView):
	template_name = 'core/help.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Help'
		return context


@method_decorator(cache_page(60*60), name='dispatch')
class Guidelines(TemplateView):
	template_name = 'core/guidelines.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Guidelines'
		return context


@method_decorator(cache_page(60*60), name='dispatch')
class FAQ(TemplateView):
	template_name = 'core/faq.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'FAQ'
		return context
