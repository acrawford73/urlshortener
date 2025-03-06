from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView


class Home(TemplateView):
	template_name = 'home/home.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Home'
		return context