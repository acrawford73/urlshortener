import random
import string
import hashlib
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView

from .models import ShortURL


class ShortenerCreateView(LoginRequiredMixin, CreateView):
	model = ShortURL
	template_name = 'shortener/shortener_form.html'
	fields = ['long_url']

class ShortenerListView(LoginRequiredMixin, ListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']

class ShortenerDetailView(LoginRequiredMixin, DetailView):
	model = ShortURL
	template_name = 'shortener/shortener_detail.html'
	context_object_name = 'link'

class ShortenerTopListView(LoginRequiredMixin, ListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-clicks']


# -----

def generate_short_alias():
	return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

@login_required
def shorten_url(request):
	if request.method == 'POST':
		long_url = request.POST.get('url')
		if not long_url:
			return JsonResponse({'error': 'URL is required'}, status=400)

		# check for existing long_url sha256
		long_url_hash = hashlib.sha256(long_url)
		if ShortURL.objects.filter(long_url_sha256=long_url_hash).exists():
			return False

		# Generate unique short alias
		short_alias = generate_short_alias()
		while ShortURL.objects.filter(short_alias=short_alias).exists():
			short_alias = generate_short_alias()

		# Save to database
		url = ShortURL.objects.create(
			short_alias=short_alias,
			long_url=long_url,
			owner=self.request.user
		)

		return JsonResponse({'short_url': f"http://psinergy.link/{short_alias}"})


def redirect_url(request, alias):
	url = get_object_or_404(ShortURL, short_alias=alias)
	# Increment click count and redirect
	url.click_count += 1
	url.save()
	return HttpResponseRedirect(url.long_url)

