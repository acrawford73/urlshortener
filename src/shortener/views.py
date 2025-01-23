import random
import string
# import hashlib
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView, DetailView
from .owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import ShortURLForm
from .models import ShortURL


class ShortenerCreateView(OwnerCreateView):
	model = ShortURL
	form_class = ShortURLForm
	template_name = 'shortener/shortener_form.html'
	#fields = ['long_url']

	def form_valid(self, form):
		short_alias = generate_unique_alias()
		while ShortURL.objects.filter(short_alias=short_alias).exists():
			short_alias = generate_unique_alias()

		# longurl = form.instance.long_url
		# url_hash = hashlib.sha256(longurl.encode())
		# long_url_sha26 = url_hash.hexdigest()
		
		form.instance.short_alias = short_alias
		# form.instance.long_url_sha26 = long_url_sha26
		return super().form_valid(form)


class ShortenerListView(OwnerListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']


class ShortenerDetailView(OwnerDetailView):
	model = ShortURL
	template_name = 'shortener/shortener_detail.html'
	context_object_name = 'link'


class ShortenerTopListView(OwnerListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-clicks']


# -----

def generate_unique_alias():
	alias = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
	if not ShortURL.objects.filter(short_alias=alias).exists():
		return alias

@login_required
def shorten_url(request):
	if request.method == 'POST':
		long_url = request.POST.get('url')
		if not long_url:
			return JsonResponse({'error': 'URL is required'}, status=400)

		# Generate unique short alias
		short_alias = generate_unique_alias()
		while ShortURL.objects.filter(short_alias=short_alias).exists():
			short_alias = generate_unique_alias()

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

