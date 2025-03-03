import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

import re
import asyncio
from playwright.async_api import async_playwright, Error
import random
import string

from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView
from django.views import View
from django.db.models import Q

from .owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import ShortURLForm, ShortURLUpdateForm
from .models import ShortURL
from taggit.models import Tag

from django.core.cache import cache
from django.views.decorators.cache import cache_page


@login_required
def tags_download(request):
	""" Download entire list of tags in system """
	tags = Tag.objects.order_by('name').values_list('name', flat=True)
	content = "\n".join(tags)
	response = HttpResponse(content, content_type="text/plain")
	response["Content-Disposition"] = 'attachment; filename="tags.txt"'
	return response


class TagsListView(LoginRequiredMixin, ListView):
	""" Show Tags List """
	model = Tag
	template_name = 'shortener/tags_list.html'
	context_object_name = 'tagslist'
	ordering = ['name']

	def get_queryset(self):
		qs = super().get_queryset()
		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(name__icontains=query)
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Tags'
		return context


@login_required
def tags_autocomplete(request):
	"""Return JSON list of tags matching the search term."""
	if 'term' in request.GET:
		term = request.GET['term']
		tags = Tag.objects.filter(name__icontains=term).values_list('name', flat=True)  # Get matching tags
		tag_list = [{'id': tag.name, 'text': tag.name} for tag in tags]  # Use tag name instead of ID
		return JsonResponse(tag_list, safe=False)
	return JsonResponse([], safe=False)


# class TagAutocompleteView(OwnerListView):
# 	def get(self, request):
# 		# query = request.GET.get('term', '')
# 		# tags = Tag.objects.filter(name__icontains=query)[:10]
# 		# return JsonResponse([{'id': tag.id, 'text': tag.name} for tag in tags], safe=False)
# 		if 'term' in request.GET:
# 			term = request.GET['term']
# 			tags = Tag.objects.filter(name__icontains=term)  # Get matching tags
# 			tag_list = [{'id': tag.name, 'text': tag.name} for tag in tags]  # Use tag name instead of ID
# 			return JsonResponse(tag_list, safe=False)
# 		return JsonResponse([], safe=False)


class ShortenerListByTagView(OwnerListView):
	""" 
	Shows owner's links by tag name. All links shown for admins.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 50

	def get_queryset(self):
		self.tag = get_object_or_404(Tag, slug=self.kwargs["tag_slug"])
		return ShortURL.objects.filter(tags__slug=self.kwargs.get('tag_slug'))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = f"Recent by Tag='{self.tag.name}'"
		return context


class ShortenerListByOwnerView(LoginRequiredMixin, ListView):
	""" Show shortened links by specific owner. """
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 50

	def get_queryset(self):
		return ShortURL.objects.filter(owner=self.kwargs.get('pk'))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Recent'
		return context


class ShortenerListView(OwnerListView):
	""" List all shortened links owned by user. """
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

		if self.request.user.is_staff:
			qs = ShortURL.objects.all() #.order_by('-created_at')  # Staff users see all short URLs
		else:
			qs = qs.filter(owner=self.request.user)  # Regular users see only their own	
		if query:
			qs = qs.filter(Q(title__icontains=query) | Q(tags__name__icontains=query)).distinct()
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Recent'
		return context


class ShortenerTopListView(OwnerListView):
	""" List all shortened links that have been clicked, descending order. """
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-clicks']
	paginate_by = 50

	def get_queryset(self):
		qs = super().get_queryset()
		query = self.request.GET.get('q')

		if self.request.user.is_staff:
			qs = ShortURL.objects.filter(clicks__gt=0).order_by('-clicks')
		else:
			qs = qs.filter(clicks__gt=0, owner=self.request.user)  # Regular users see only their own	
		
		if query:
			qs = qs.filter(Q(title__icontains=query) | Q(tags__name__icontains=query)).distinct()
		return qs
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Top'
		return context


class ShortenerCreateView(OwnerCreateView):
	""" Create a new shortened link. """
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
			messages.warning(self.request, "This URL was already shortened.")
			return redirect('shortener-detail', pk=existing.pk)

		# Check if anyone else shortened this link already
		existing = ShortURL.objects.filter(long_url=url).first()
		if existing:
			messages.warning(self.request, "This URL was already shortened.")
			return redirect('shortener-detail-exists', pk=existing.pk)

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

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Create'
		return context


class ShortenerDetailView(OwnerDetailView):
	""" ShortURL detail view. """
	model = ShortURL
	template_name = 'shortener/shortener_detail.html'
	context_object_name = 'link'

	def get_queryset(self):
		# If the user is staff, allow access to ANY short URL
		if self.request.user.is_staff:
			return ShortURL.objects.all()
		# Otherwise, restrict to links owned by the current user only
		return ShortURL.objects.filter(owner=self.request.user)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"{short_alias}"
		return context


class ShortenerDetailExistsView(LoginRequiredMixin, DetailView):
	""" 
	ShortURL detail view for link that already exists.
	Presented when the ShortURL is from another user.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_detail.html'
	context_object_name = 'link'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"{short_alias}"
		return context


class ShortenerUpdateView(OwnerUpdateView):
	""" ShortURL update view. """
	model = ShortURL
	form_class = ShortURLUpdateForm
	template_name = 'shortener/shortener_update.html'
	context_object_name = 'link'
	#success_url = reverse_lazy('shortener-detail')

	def get_queryset(self):
		# Allow staff to update any short URL, others only their own
		if self.request.user.is_staff:
			return ShortURL.objects.all()
		return ShortURL.objects.filter(owner=self.request.user)

	def get_success_url(self):
		# Capture the page number from the GET request, default to 1
		page = self.request.GET.get('page', 1)
		query = self.request.GET.get('q', '')
		if query:
			return f"{reverse('shortener-list')}?page={page}&q={query}"
		return f"{reverse('shortener-list')}?page={page}"
		#return f"{reverse('shortener-detail', kwargs={'pk': self.object.pk})}?page={page}"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"Update {short_alias}"
		return context


class ShortenerDeleteView(OwnerDeleteView):
	""" ShortURL delete view. """
	model = ShortURL
	template_name = 'shortener/shortener_confirm_delete.html'
	context_object_name = 'link'
	#success_url = reverse_lazy('shortener-list')

	def get_queryset(self):
		# Allow staff to delete any short URL, others only their own
		if self.request.user.is_staff:
			return ShortURL.objects.all()
		return ShortURL.objects.filter(owner=self.request.user)

	def get_success_url(self):
		page = self.request.GET.get('page', 1)
		query = self.request.GET.get('q', '')
		if query:
			return f"{reverse('shortener-list')}?page={page}&q={query}"
		return f"{reverse('shortener-list')}?page={page}"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"Delete {short_alias}"
		return context


# - - - - -


# Check for specific search engines based on common regex
def search_check(search_domain, search_url):
	title = None
	if re.search(search_domain, search_url):
		# Get text between "q=" and w/wo "&"
		match = re.search(r"q=([^&]+)(?:&|$)", search_url)
		if match:
			result = unquote(match.group(1))
			title = result.replace("+"," ")
	return title


# Capture the title of the long url that is being shortened
def get_page_title(url):
	""" Process that captures the title of a website page. """
	title = None

	## Specific Cases (Level 1)
	# Cannot reliably get the title tag from search results page
	# Grab from the search parameter

	search_url = url

	# Google Patents
	if re.search(r'patents\.google\.[^/]+/\?', search_url):
		match = re.search(r"q=\(([^)]+)\)(?:&|$)", search_url)
		if match:
			result = unquote(match.group(1))
			title = result.replace("+"," ")
			return str(title) + " - Google Patents Search"

	# Google
	title = search_check(r'google\.[^/]+/search\?', search_url)
	if title:
		return str(title) + " - Google Search"

	# Brave
	title = search_check(r'search\.brave\.[^/]+/search\?', search_url)
	if title:
		return str(title) + " - Brave Search"

	# DuckDuckGo
	title = search_check(r'duckduckgo\.[^/]+/\?', search_url)
	if title:
		return str(title) + " - DuckDuckGo Search"

	# # Google Search, format (*google.*/search?)
	# if re.search(r'google\.[^/]+/search\?', search_url):
	# 	# Get text between "q=" and w/wo "&"
	# 	match = re.search(r"q=([^&]+)(?:&|$)", search_url)
	# 	if match:
	# 		result = unquote(match.group(1))
	# 		title = result.replace("+"," ")
	# 		return str(title) + " - Google Search"

	# # Brave Search
	# if re.search(r'search\.brave\.[^/]+/search\?', search_url):
	# 	match = re.search(r"q=([^&]+)(?:&|$)", search_url)
	# 	if match:
	# 		result = unquote(match.group(1))
	# 		title = result.replace("+"," ")
	# 		return str(title) + " - Brave Search"

	# # DuckDuckGo Search
	# if re.search(r'duckduckgo\.[^/]+/\?', search_url):
	# 	match = re.search(r"q=([^&]+)(?:&|$)", search_url)
	# 	if match:
	# 		result = unquote(match.group(1))
	# 		title = result.replace("+"," ")
	# 		return str(title) + " - DuckDuckGo Search"


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
	""" Browser simulator to acquire website page title. """
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


def generate_unique_alias(url):
	""" Generates the unique alias code"""
	alias = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
	## alias_code + domain
	#alias_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
	#domain = urlparse(url).netloc  # www.domain.com
	#host = '.'.join(domain.split('.')[-2:])  # domain.com
	#aname = host.split('.')[0]  # domain
	#alias = alias_code + "-" + aname
	if not ShortURL.objects.filter(short_alias=alias).exists():
		return alias


@cache_page(60 * 60)  # Cache for 1 hour
def redirect_url(request, alias):
	""" Redirect all ShortURL clicks to the original URL. """
	url = get_object_or_404(ShortURL, short_alias=alias)
	url.clicks += 1
	url.save()
	return HttpResponseRedirect(url.long_url)

