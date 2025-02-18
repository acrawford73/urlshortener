import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

import re
import asyncio
from playwright.async_api import async_playwright, Error
import random
import string

from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView, DetailView
from .owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import ShortURLForm
from .models import ShortURL

from django.core.cache import cache
from django.views.decorators.cache import cache_page


class ShortenerCreateView(OwnerCreateView):
	model = ShortURL
	form_class = ShortURLForm
	template_name = 'shortener/shortener_form.html'

	def get_success_url(self):
		return reverse('shortener-detail', kwargs={'pk': self.object.pk})

	def form_valid(self, form):
		url = form.cleaned_data['long_url']

		# Check if owner shortened this link already
		existing = ShortURL.objects.filter(long_url=url, owner=self.request.user).first()
		if existing:
			return redirect('shortener-detail', pk=existing.pk)

		# Check if anyone shortened this link already
		existing = ShortURL.objects.filter(long_url=url).first()
		if existing:	
			return redirect('shortener-detail', pk=existing.pk)

		title = get_page_title(url)

		short_alias = generate_unique_alias(url)
		while ShortURL.objects.filter(short_alias=short_alias).exists():
			short_alias = generate_unique_alias(url)

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
	paginate_by = 50

	def get_queryset(self):
		# Get the base queryset from the parent view
		qs = super().get_queryset()
		# Get the search query from the GET parameters (e.g., ?q=search_term)
		query = self.request.GET.get('q')
		if query:
			# Filter by title using case-insensitive containment lookup
			qs = qs.filter(title__icontains=query, owner=self.request.user)
		return qs


class ShortenerTopListView(OwnerListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-clicks']
	paginate_by = 50

	def get_queryset(self):
		qs = super().get_queryset()
		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(title__icontains=query, owner=self.request.user)
		else:
			qs = qs.filter(clicks__gt=0, owner=self.request.user)
		return qs


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
def get_page_title(url):
	title = None

	## Specific Cases (Level 1)
	# Google Search
	# Cannot reliably get the title tag so just grab it from the search parameter
	google_url = url
	# First check for Google search format (*google.*/search?)
	if re.search(r'google\.[^/]+/search\?', google_url):
		# Get text between "q=" and w/wo "&"
		match = re.search(r"q=([^&]+)(?:&|$)", google_url)
		if match:
			result = match.group(1)
			title = result.replace("+"," ")
			return str(title) + " - Google Search"

	# Google Patents Search
	if re.search(r'patents\.google\.[^/]+/\?', google_url):
		match = re.search(r"q=\(([^)]+)\)(?:&|$)", google_url)
		if match:
			result = match.group(1)
			title = result.replace("+"," ")
			return str(title) + " - Google Patents Search"

	## Requests & BeautifulSoup (Level 2)
	host_url = url
	domain = urlparse(host_url).netloc
	#server_host = '.'.join(domain.split('.')[-2:])
	server_host = domain

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
		response = rs.get(url, timeout=10, allow_redirects=True, headers=headers)
		response.raise_for_status()

		# Check raw title tags first
		match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
		if match:
			title = match.group(1)
			rs.close()
			return title.strip()[:255]

		# BS4 then
		soup = BeautifulSoup(response.text, 'html.parser')
		soup_title = soup.select_one("title")
		if soup_title:
			title = soup_title.text.strip()[:255]
			rs.close()
			return title
	except requests.exceptions.HTTPError as err:
		print(f'HTTP Error: {err}')
	except requests.exceptions.ConnectionError as errc:
		print(f'Error Connecting: {errc}')
	except requests.exceptions.Timeout as errt:
		print(f'Timeout Error: {errt}')
	except requests.exceptions.TooManyRedirects as errtm:
		print(f'Too Many Redirects: {errtm}')
	except requests.exceptions.RequestException as errre:
		print(f'Oops: Something Else: {errre}')				
	finally:
		rs.close()

	## Browser Simulator - final attempt (Level 4)
	title = asyncio.run(async_get_title_playwright(url))
	return title


# https://playwright.dev/docs/api/class-page
async def async_get_title_playwright(url):
	title = None
	try:
		async with async_playwright() as p:
			browser = await p.chromium.launch(headless=True)  # Set headless=False if you want to see the browser
			context = await browser.new_context()
			page = await context.new_page()
			page.set_default_navigation_timeout(30000.0) # no await needed
			# Filter out media content, not necessary for HTML parsing
			await page.route(re.compile(r"\.(qt|mov|mp4|mpg|m4v|m4a|mp3|ogg|jpeg|jpg|png|gif|svg|webp|wott|woff|otf|eot)$"), lambda route: route.abort()) 
			await page.goto(url)
			title = await page.title()
			title = title.strip()[:255]
	except Error as err:
		print(f"Error occurred: {err}")
	except Exception as e:
		print(f"Exception occurred: {e}")
	finally:
		await browser.close()
	return title


# Generate the unique alias code
def generate_unique_alias(url):
	alias = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
	## alias_code + domain
	#alias_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
	#domain = urlparse(url).netloc  # www.domain.com
	#host = '.'.join(domain.split('.')[-2:])  # domain.com
	#aname = host.split('.')[0]  # domain
	#alias = alias_code + "-" + aname
	if not ShortURL.objects.filter(short_alias=alias).exists():
		return alias


# Redirect the shortened link to the original URL
@cache_page(60 * 60)  # Cache for 1 hour
def redirect_url(request, alias):
	url = get_object_or_404(ShortURL, short_alias=alias)
	url.clicks += 1
	url.save()
	return HttpResponseRedirect(url.long_url)

