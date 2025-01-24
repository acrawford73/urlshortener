import requests
from django.utils.html import strip_tags
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import random
import string
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
	success_url = reverse_lazy('shortener-list')

	def form_valid(self, form):
		url = form.cleaned_data['long_url']
		title = get_title(url)

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
def get_title(url):
	title = None

	host_url = url
	domain = urlparse(host_url).netloc
	server_host = '.'.join(domain.split('.')[-2:])
	headers = {
		'Host': server_host,
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-US;q=0.7,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate, br, zstd',
		'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
		'Connection':'keep-alive',
		'Cache-Control': 'max-age=0',
		'Upgrade-Insecure-Requests': '1',
	}

	try:
		rs = requests.Session()
		response = rs.get(url, timeout=10, headers=headers) #allow_redirects=False, headers=headers)
		response.raise_for_status()
		# if response.status_code in (301, 302):
		# 	new_location = response.headers['Location']
		# 	print(f'Redirect to {new_location}')
		# 	response = rs.get(new_location, timeout=10, allow_redirects=False, headers=headers)
		# 	response.raise_for_status()
		soup = BeautifulSoup(response.text, 'html.parser')
		
		# Attempt 1
		title_tag = soup.title
		if title_tag:
			title = strip_tags(title_tag.text)[:255]
			print("soup.title = " + title)
			rs.close()
			return title

		# Attempt 2
		title_tag = soup.find("title")
		if title_tag:
			title = strip_tags(title_tag.text)[:255]
			print("soup.find = " + title)
			rs.close()
			return title

		# Attempt 3
		tags = soup.find("meta")
		for tag in tags:
			if tag.get('property', None) == "og:title":
				title = tag.get('content', None)[:255]
				print("og:title = " + title)
		rs.close()
		return title

	except requests.exceptions.HTTPError as err:
		print(f'HTTP Error: {err}')
	except requests.exceptions.ConnectionError as errc:
		print(f'Error Connecting: {errc}')
	except requests.exceptions.Timeout as errt:
		print(f'Timeout Error: {errt}')
	except requests.exceptions.RequestException as errr:
		print(f'Oops: Something Else: {errr}')				
	finally:
		rs.close()
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

