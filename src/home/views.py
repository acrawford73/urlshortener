from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView


class Home(TemplateView):
	template_name = 'home/home.html'

