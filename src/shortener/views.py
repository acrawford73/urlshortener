import time
import json
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
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.views import View
from django.db.models import Q

from .owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import ShortURLForm, ShortURLUpdateForm
from .models import ShortURL
from taggit.models import Tag

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from functools import wraps


# -----


def throttle_view(rate, per):
	"""Throttle redirect requests"""
	def decorator(view_func):
		@wraps(view_func)
		def wrapped(request, *args, **kwargs):
			ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')).split(',')[0]
			key = f"throttle:{ip}"
			history = cache.get(key, [])
			now = time.time()

			# Filter timestamps older than the window
			history = [t for t in history if now - t < per]

			if len(history) >= rate:
				response = HttpResponse("Rate limit exceeded", status=429)
				response["Retry-After"] ="600"
				return response

			history.append(now)
			cache.set(key, history, timeout=per)
			return view_func(request, *args, **kwargs)
		return wrapped
	return decorator


@throttle_view(rate=60, per=60)  # 60 requests per IP per minute
@cache_page(60 * 60, key_prefix='redirect_url')  # Cache for one hour
def redirect_url(request, alias):
	"""Redirect all ShortURL clicks to the original URL."""
	url = get_object_or_404(ShortURL, short_alias=alias)
	return HttpResponseRedirect(url.long_url)


@login_required
def tags_download(request):
	""" Download list of all tags in system """
	tags = Tag.objects.order_by('name').values_list('name', flat=True)
	content = '\n'.join(tags)
	response = HttpResponse(content, content_type='text/plain')
	response['Content-Disposition'] = 'attachment; filename="topics.txt"'
	return response


class TagsListView(ListView):
	""" Show Tags List """
	model = Tag
	template_name = 'shortener/tags_list.html'
	context_object_name = 'tagslist'
	ordering = ['slug']

	def get_queryset(self):
		qs = super().get_queryset()
		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(name__icontains=query)
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Topics'
		return context


# @login_required
# def tags_suggestions(request):
# 	"""Return JSON list of tags matching the context-sensitive term."""
# 	if 'term' in request.GET:
# 		term = request.GET.get('term', '')
# 		tags = Tag.objects.filter(name__icontains=term).values_list('name', flat=True)[:10]
# 		suggestions = [{'id': tag.name, 'text': tag.name} for tag in tags]
# 		return JsonResponse(suggestions, safe=False)
# 	return JsonResponse([], safe=False)


@require_GET
@login_required
def tags_suggestions(request):
	term = request.GET.get('term', '').strip()
	context = request.GET.get('context')  # You can use this to filter based on context if needed
	qs = Tag.objects.all()
	if term:
		qs = qs.filter(name__istartswith=term)
		#qs = qs.filter(name__icontains=term)
	tags = qs.order_by('name').values_list('name', flat=True).distinct()[:10]
	return JsonResponse(list(tags), safe=False)



CACHE_TTL = 60 * 30

@method_decorator(cache_page(CACHE_TTL), name='dispatch')
class ShortenerListViewOpen(ListView):
	"""
	List all shortened links, no login, PUBLIC.
	Private links are skipped.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list_open.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 50

	def get_queryset(self):
		qs = super().get_queryset()
		#qs = qs.select_related('owner').prefetch_related('tags').filter(private=False)
		qs = qs.prefetch_related('tags').filter(private=False)
		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(Q(title__icontains=query) | Q(tags__name__icontains=query)).distinct()
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		#context['page_title'] = 'Recent Links'
		context['total_results'] = self.get_queryset().count()
		return context


@method_decorator(cache_page(CACHE_TTL), name='dispatch')
class ShortenerListByTagViewOpen(ListView):
	""" 
	Shows links by tag name, no login, PUBLIC.
	Private links are skipped.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list_open.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 50

	def get_queryset(self):
		qs = super().get_queryset()
		self.tag = get_object_or_404(Tag, slug=self.kwargs['tag_slug'])
		return qs.prefetch_related('tags').filter(tags__slug=self.kwargs.get('tag_slug')).filter(private=False)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = f"Links by Topic='{self.tag.name}'"
		context['total_results'] = self.get_queryset().count()
		return context


class ShortenerAllListByTagView(LoginRequiredMixin, ListView):
	""" 
	Shows all links by tag name.
	Private links are skipped.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list_all.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		qs = super().get_queryset()
		self.tag = get_object_or_404(Tag, slug=self.kwargs['tag_slug'])
		return qs.select_related('owner').prefetch_related('tags').filter(tags__slug=self.kwargs.get('tag_slug')).filter(private=False)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = f"Links by Topic='{self.tag.name}'"
		context['total_results'] = self.get_queryset().count()
		return context


class ShortenerListByTagView(OwnerListView):
	""" 
	Shows owner's links by tag name.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		qs = super().get_queryset()
		self.tag = get_object_or_404(Tag, slug=self.kwargs['tag_slug'])
		return qs.select_related('owner').prefetch_related('tags').filter(tags__slug=self.kwargs.get('tag_slug'))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = f"My Links by Topic='{self.tag.name}'"
		context['total_results'] = self.get_queryset().count()
		return context


class ShortenerAllByOwnerListView(LoginRequiredMixin, ListView):
	"""
	Show shortened links by ANY user.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list_all.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		qs = super().get_queryset()
		qs = qs.select_related('owner').prefetch_related('tags').filter(owner=self.kwargs.get('pk'))
		# When selecting by user: 
		# - don't show private links for other users
		# - show your own private links
		if str(self.request.user.pk) != str(self.kwargs.get('pk')):
			qs = qs.filter(private=False)
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Links'
		context['total_results'] = self.get_queryset().count()
		return context


class ShortenerByOwnerListView(OwnerListView):
	"""
	Show shortened links by owner/user.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		qs = super().get_queryset()
		return qs.select_related('owner').prefetch_related('tags').filter(owner=self.kwargs.get('pk'))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'My Links'
		context['total_results'] = self.get_queryset().count()
		return context


class ShortenerListView(OwnerListView):
	"""
	List all shortened links owned by a user.
	"""
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		# Get the base queryset from the parent view
		qs = super().get_queryset()
		qs = qs.select_related('owner').prefetch_related('tags')
		# Get the search query from the GET parameters (e.g., ?q=search_term)
		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(Q(title__icontains=query) | Q(tags__name__icontains=query)).distinct()
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'My Links'
		context['total_results'] = self.get_queryset().count()
		return context


class ShortenerAllListView(LoginRequiredMixin, ListView):
	""" List all shortened links. Ignore private links. """
	model = ShortURL
	template_name = 'shortener/shortener_list_all.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		qs = super().get_queryset()

		qs = qs.select_related('owner').prefetch_related('tags')
		qs = qs.filter(Q(private=False) | Q(owner=self.request.user))

		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(Q(title__icontains=query) | Q(tags__name__icontains=query)).distinct()
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'All Links'
		context['total_results'] = self.get_queryset().count()
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
			messages.warning(self.request, "Thanks, but this link is already shortened.")
			return redirect('shortener-detail', pk=existing.pk)

		# Check if anyone else shortened this link already
		existing = ShortURL.objects.filter(long_url=url).first()
		if existing:
			messages.warning(self.request, "Thanks, but this link is already shortened.")
			return redirect('shortener-detail-all', pk=existing.pk)

		title = get_page_title(url)

		# Limit alias generations, prevent infinte loop
		MAX_ATTEMPTS = 30
		attempts = 0
		short_alias = generate_unique_alias(url)
		while ShortURL.objects.filter(short_alias=short_alias).exists():
			attempts += 1
			if attempts >= MAX_ATTEMPTS:
				print("Failed unique alias generation!")
				contnue
			short_alias = generate_unique_alias(url)

		shorturl = form.save(commit=False)
		shorturl.owner = self.request.user
		if title != None:
			shorturl.title = title
			if title.startswith("Direct link to"):
				shorturl.private = True
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
		qs = super().get_queryset()
		# If the user is staff, allow access to ANY short URL (handled in owner.py)
		return qs.select_related('owner').prefetch_related('tags')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"{short_alias}"
		return context


class ShortenerAllDetailView(LoginRequiredMixin, DetailView):
	""" ShortURL detail view for non-owner links. """
	model = ShortURL
	template_name = 'shortener/shortener_detail_all.html'
	context_object_name = 'link'

	def get_queryset(self):
		qs = super().get_queryset()
		return qs.select_related('owner').prefetch_related('tags')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"{short_alias}"
		return context


class ShortenerUpdateView(OwnerUpdateView):
	""" ShortURL update view by owner. """
	model = ShortURL
	form_class = ShortURLUpdateForm
	template_name = 'shortener/shortener_update.html'
	context_object_name = 'link'
	#success_url = reverse_lazy('shortener-detail')

	def get_queryset(self):
		qs = super().get_queryset()
		# Allow staff to update any short URL, others only their own
		return qs.select_related('owner').prefetch_related('tags')

	def get_success_url(self):
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


class ShortenerAllUpdateView(LoginRequiredMixin, UpdateView):
	""" ShortURL update view. """
	model = ShortURL
	form_class = ShortURLUpdateForm
	template_name = 'shortener/shortener_update_all.html'
	context_object_name = 'link'

	def get_queryset(self):
		qs = super().get_queryset()
		return qs.select_related('owner').prefetch_related('tags')

	def get_success_url(self):
		page = self.request.GET.get('page', 1)
		query = self.request.GET.get('q', '')
		if query:
			return f"{reverse('shortener-list-all')}?page={page}&q={query}"
		return f"{reverse('shortener-list-all')}?page={page}"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"Update {short_alias}"
		return context


class ShortenerDeleteView(OwnerDeleteView):
	"""ShortURL delete view for owner's links."""
	model = ShortURL
	template_name = 'shortener/shortener_confirm_delete.html'
	context_object_name = 'link'
	#success_url = reverse_lazy('shortener-list')

	def get_queryset(self):
		qs = super().get_queryset()
		# Allow staff to delete any short URL, others only their own
		return qs.select_related('owner').prefetch_related('tags')

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


class ShortenerAllDeleteView(OwnerDeleteView):
	"""ShortURL delete view."""
	model = ShortURL
	template_name = 'shortener/shortener_confirm_delete_all.html'
	context_object_name = 'link'
	#success_url = reverse_lazy('shortener-list')

	def get_queryset(self):
		qs = super().get_queryset()
		# Allow staff to delete any short URL, others only their own
		return qs.select_related('owner').prefetch_related('tags')

	def get_success_url(self):
		page = self.request.GET.get('page', 1)
		query = self.request.GET.get('q', '')
		if query:
			return f"{reverse('shortener-list-all')}?page={page}&q={query}"
		return f"{reverse('shortener-list-all')}?page={page}"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		short_alias = self.object.short_alias
		context['page_title'] = f"Delete {short_alias}"
		return context


# - - - - -


# Precompile regex patterns for better performance
SEARCH_PATTERNS = {
	"google": re.compile(r"google\.[^/]+/search\?"),
	"brave": re.compile(r"search\.brave\.[^/]+/search\?"),
	"duckduckgo": re.compile(r"duckduckgo\.[^/]+/\?")
	# more search engines...
}

QUERY_PATTERN = re.compile(r"q=([^&]+)(?:&|$)")
#PATENTS_QUERY_PATTERN = re.compile(r"q=\(([^)]+)\)(?:&|$)")


def extract_query_param(url, pattern):
	match = pattern.search(url)
	return unquote(match.group(1)).replace('+', ' ').strip()[:475] if match else None


# Check for specific search engines based on common regex
def search_check(search_domain, search_url):
	"""Extracts the search query from a given search URL."""
	if search_domain.search(search_url):
		return extract_query_param(search_url, QUERY_PATTERN)
	return None


DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.m4v'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a', '.wma'}
ALL_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

def is_direct_file_link(url: str) -> bool:
	path = urlparse(url).path.lower()
	for ext in ALL_EXTENSIONS:
		if path.endswith(ext):
			return ext
	return None


def get_page_title(url):
	"""Fetches the title of a given URL webpage."""

	## Level 1
	# Check direct links to files
	ext = is_direct_file_link(url)
	if ext:
		return f"Direct link to {ext.split('.')[1].upper()} file! Please rename this Title field."

	## Level 2
	# Check search engines
	for name, pattern in SEARCH_PATTERNS.items():
		if title := search_check(pattern, url):
			return f"{title} - {name.capitalize()} Search"

	# Google Patents specific case
	if re.search(r'patents\.google\.[^/]+/\?', url):
		match = re.search(r'q=\(([^)]+)\)(?:&|$)', url)
		if match:
			title = unquote(match.group(1)).replace('\n','').replace('+', ' ').strip()[:475]
			return f"{title} - Google Patents Search"

	## Level 2 or 3
	# Fallback: Try to fetch the page title
	return fetch_title_from_html(url) or asyncio.run(async_get_title_playwright(url))


## Level 3 - Requests & BS4
def fetch_title_from_html(url):
	host_url = url
	server_host = urlparse(host_url).netloc

	"""Attempts to retrieve the title using requests and BeautifulSoup."""
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
		with requests.Session() as session:
			response = session.get(url, timeout=10, allow_redirects=True, headers=headers)
			response.raise_for_status()
			soup = BeautifulSoup(response.text, 'html.parser')
			title_tag = soup.select_one("title")
			if title_tag:
				return unquote(title_tag.text.strip())[:500]
	except requests.exceptions.RequestException as err:
		print(f"Request error: {err}")
	finally:
		session.close()
	return None


## Level 4 - Browser Simulator
async def async_get_title_playwright(url):
	"""Fetches the title using Playwright for JavaScript-rendered pages."""
	try:
		async with async_playwright() as p:
			browser = await p.chromium.launch(headless=True)
			context = await browser.new_context()
			page = await context.new_page()
			page.set_default_navigation_timeout(30000)
			await page.route(re.compile(r"\.(asx|m3u|m3u8|ts|qt|mov|mp4|mpg|m4v|m4a|mp3|ogg|jpeg|jpg|png|gif|svg|webp|wott|woff|otf|eot)$"), lambda route: route.abort())
			await page.goto(url)
			title = await page.title()
			await browser.close()
			return unquote(title.strip())[:500]
	except Exception as e:
		print(f"Playwright error: {e}")
	return None




# # Capture the title of the long url that is being shortened
# def get_page_title(url):
# 	"""Process that captures the title of a website page."""
# 	title = None

# 	## Specific Cases (Level 1)
# 	# Cannot reliably get the title tag from search results page
# 	# Grab from the search parameter

# 	search_url = url

# 	# Google Patents
# 	if re.search(r'patents\.google\.[^/]+/\?', search_url) or re.search(r'patents\.google\.[^/]+/patent/', search_url):
# 		match = re.search(r'q=\(([^)]+)\)(?:&|$)', search_url)
# 		if match:
# 			result = unquote(match.group(1))
# 			title = result.replace('+',' ')
# 			title = title.strip()[:475]
# 			return f"{title} - Google Patents Search"

# 	# Google
# 	title = search_check(r'google\.[^/]+/search\?', search_url)
# 	if title:
# 		return f"{title} - Google Search"

# 	# Brave
# 	title = search_check(r'search\.brave\.[^/]+/search\?', search_url)
# 	if title:
# 		return f"{title} - Brave Search"

# 	# DuckDuckGo
# 	title = search_check(r'duckduckgo\.[^/]+/\?', search_url)
# 	if title:
# 		return f"{title} - DuckDuckGo Search"

# 	## Requests & BeautifulSoup (Level 2)
# 	host_url = url
# 	domain = urlparse(host_url).netloc
# 	#server_host = '.'.join(domain.split('.')[-2:])
# 	server_host = domain

# 	headers = {
# 		'Host': server_host,
# 		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
# 		'Accept-Language': 'en-US;q=0.7,en;q=0.3',
# 		'Accept-Encoding': 'gzip, deflate, br, zstd',
# 		'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
# 		'Connection':'keep-alive',
# 		'Cache-Control': 'max-age=0',
# 		'Upgrade-Insecure-Requests': '1',
# 	}

# 	try:
# 		rs = requests.Session()
# 		response = rs.get(url, timeout=10, allow_redirects=True, headers=headers)
# 		response.raise_for_status()

# 		# Check raw title tags first
# 		match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
# 		if match:
# 			title = unquote(match.group(1))
# 			rs.close()
# 			return title.strip()[:500]

# 		# BS4 then
# 		soup = BeautifulSoup(response.text, 'html.parser')
# 		soup_title = soup.select_one("title")
# 		if soup_title != None:
# 			title = soup_title.text.strip()[:500]
# 			title = unquote(title)
# 			rs.close()
# 			return title
# 	except requests.exceptions.HTTPError as err:
# 		print(f'HTTP Error: {err}')
# 	except requests.exceptions.ConnectionError as errc:
# 		print(f'Error Connecting: {errc}')
# 	except requests.exceptions.Timeout as errt:
# 		print(f'Timeout Error: {errt}')
# 	except requests.exceptions.TooManyRedirects as errtm:
# 		print(f'Too Many Redirects: {errtm}')
# 	except requests.exceptions.RequestException as errre:
# 		print(f'Oops: Something Else: {errre}')				
# 	finally:
# 		rs.close()

# 	## Browser Simulator - final attempt (Level 4)
# 	title = asyncio.run(async_get_title_playwright(url))
# 	return title


# # https://playwright.dev/docs/api/class-page
# async def async_get_title_playwright(url):
# 	"""Browser simulator to acquire website page title."""
# 	title = None
# 	try:
# 		async with async_playwright() as p:
# 			browser = await p.chromium.launch(headless=True)  # Set headless=False if you want to see the browser
# 			context = await browser.new_context()
# 			page = await context.new_page()
# 			page.set_default_navigation_timeout(30000.0) # no await needed
# 			# Filter out media content, not necessary for HTML parsing
# 			await page.route(re.compile(r"\.(asx|m3u|m3u8|ts|qt|mov|mp4|mpg|m4v|m4a|mp3|ogg|jpeg|jpg|png|gif|svg|webp|wott|woff|otf|eot)$"), lambda route: route.abort()) 
# 			await page.goto(url)
# 			title = await page.title()
# 			title = unquote(title)
# 			title = title.strip()[:500]
# 	except Error as err:
# 		print(f"Error occurred: {err}")
# 	except Exception as e:
# 		print(f"Exception occurred: {e}")
# 	finally:
# 		await browser.close()
# 	return title


def generate_unique_alias(url):
	"""Generates the unique alias code."""
	alias = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
	if not ShortURL.objects.filter(short_alias=alias).exists():
		return alias


## RSS Feed
class ShortURLRSSFeed(Feed):
	title = "BioDigCon.link RSS Feed"
	link = "/feed/rss/"
	description = "Recent curated links"
	feed_copyright = "2025 BIODIGCON.LINK"
	ttl = 600
	def items(self):
		return ShortURL.objects.prefetch_related('tags').filter(private=False).order_by('-created_at')[:50]
	def item_title(self, item):
		return item.title
	def item_description(self, item):
		description = ", ".join(str(tag) for tag in item.tags.all())
		return description
	def item_link(self, item):
		return f"/{item.short_alias}/"
	def item_author_name(self, item):
		return "Researchers"
	def item_guid(self, item):
		return str(item.id).lower()
	def item_pubdate(self, item):
		return item.created_at
	def item_categories(self, item):
		return [str(tag) for tag in item.tags.all()]
	def get_feed(self, obj, request):
		feedgen = super().get_feed(obj, request)
		feedgen.content_type = "application/xml; charset=utf-8"
		return feedgen

class ShortURLAtomFeed(ShortURLRSSFeed):
	feed_type = Atom1Feed
	subtitle = ShortURLRSSFeed.description
