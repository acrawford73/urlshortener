from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView


class Terms(TemplateView):
	template_name = 'core/terms.html'

class Privacy(TemplateView):
	template_name = 'core/privacy.html'

class Help(TemplateView):
	template_name = 'core/help.html'

class License(TemplateView):
	template_name = 'core/license.html'