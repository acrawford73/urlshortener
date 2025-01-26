import random
import string
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView, DetailView
from .owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import ShortURLForm
from .models import ShortURL

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options


class ShortenerCreateView(OwnerCreateView):
	model = ShortURL
	form_class = ShortURLForm
	template_name = 'shortener/shortener_form.html'
	success_url = reverse_lazy('shortener-list')

	def form_valid(self, form):
		url = form.cleaned_data['long_url']
		
		title = None
		title = get_soap_title(url)

		short_alias = generate_unique_alias()
		while ShortURL.objects.filter(short_alias=short_alias).exists():
			short_alias = generate_unique_alias()
		
		shorturl = form.save(commit=False)
		shorturl.owner = self.request.user
		shorturl.title = title
		shorturl.short_alias = short_alias
		shorturl.save()
		form.save_m2m()
		return super().form_valid(form)

class ShortenerListView(OwnerListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']

class ShortenerTopListView(OwnerListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-clicks']

class ShortenerDetailView(OwnerDetailView):
	model = ShortURL
	template_name = 'shortener/shortener_detail.html'
	context_object_name = 'link'

class ShortenerUpdateView(OwnerUpdateView):
	model = ShortURL
	template_name = 'shortener/shortener_update.html'
	context_object_name = 'link'
	fields = ['title', 'long_url']

class ShortenerDeleteView(OwnerDeleteView):
	model = ShortURL
	template_name = 'shortener/shortener_confirm_delete.html'
	context_object_name = 'link'
	success_url = reverse_lazy('shortener-list')


# - - - - -

# Capture the title of the long url that is being shortened
def get_soap_title(url):
	title = None
	
	# try the soup method first, then selenium as last resort


	# Set up options for Firefox
	# Only needed if Firefox is in a custom location
	firefox_binary_path = settings.FIREFOX_PATH
	options = Options()
	options.binary_location = firefox_binary_path
	options.add_argument('--no-sandbox')
	options.add_argument('--headless')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--headless')
	options.add_argument('--disable-gpu')

	# Set up the GeckoDriver service
	# Download Gecko driver from github.com/mozilla/geckodriver/releases
	service = Service(settings.GECKO_PATH)

	driver = webdriver.Firefox(service=service, options=options)
	driver.get(url)
	title = driver.title[:255]
	driver.quit()
	return title


# Generate the unique alias code
def generate_unique_alias():
	alias = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
	if not ShortURL.objects.filter(short_alias=alias).exists():
		return alias


# Shorten the original URL
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


# Redirect the shortened link to the original URL
def redirect_url(request, alias):
	url = get_object_or_404(ShortURL, short_alias=alias)
	# Increment click count and redirect
	url.clicks += 1
	url.save()
	return HttpResponseRedirect(url.long_url)

