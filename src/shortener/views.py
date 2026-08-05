from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.db.models import F, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, ListView

from taggit.models import Tag

from .forms import ShortURLForm, ShortURLUpdateForm
from .models import ShortURL
from .owner import (
	OwnerCreateView,
	OwnerDeleteView,
	OwnerDetailView,
	OwnerListView,
	OwnerUpdateView,
	is_visible_to_user,
	paginated_total,
	visible_shorturls,
)
from .tasks import fetch_title_task
from .utils.aliases import generate_unique_alias
from .utils.throttle import check_rate_limit
from .utils.titles import fetch_title_fast


REDIRECT_CACHE_TTL = 60 * 60


def throttle_view(rate, per):
	"""Throttle requests using an atomic cache counter."""
	def decorator(view_func):
		@wraps(view_func)
		def wrapped(request, *args, **kwargs):
			if not check_rate_limit(request, 'throttle:redirect', rate, per):
				response = HttpResponse("Rate limit exceeded", status=429)
				response["Retry-After"] = "60"
				return response
			return view_func(request, *args, **kwargs)
		return wrapped
	return decorator


@throttle_view(rate=60, per=60)
def redirect_url(request, alias):
	"""Redirect ShortURL clicks to the original URL."""
	cache_key = f"redirect:{alias}"
	cached = cache.get(cache_key)

	if cached is not None:
		if cached == '':
			raise Http404
		ShortURL.objects.filter(short_alias=alias, private=False).update(clicks=F('clicks') + 1)
		return HttpResponseRedirect(cached)

	shorturl = get_object_or_404(ShortURL, short_alias=alias)
	if shorturl.private:
		cache.set(cache_key, '', timeout=REDIRECT_CACHE_TTL)
		raise Http404

	cache.set(cache_key, shorturl.long_url, timeout=REDIRECT_CACHE_TTL)
	ShortURL.objects.filter(pk=shorturl.pk).update(clicks=F('clicks') + 1)
	return HttpResponseRedirect(shorturl.long_url)


@login_required
def tags_download(request):
	tags = Tag.objects.order_by('name').values_list('name', flat=True)
	content = '\n'.join(tags)
	response = HttpResponse(content, content_type='text/plain')
	response['Content-Disposition'] = 'attachment; filename="topics.txt"'
	return response


class TagsListView(LoginRequiredMixin, ListView):
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


class TagsListViewOpen(ListView):
	model = Tag
	template_name = 'shortener/tags_list_open.html'
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


@require_GET
@login_required
def tags_suggestions(request):
	term = request.GET.get('term', '').strip()
	qs = Tag.objects.all()
	if term:
		qs = qs.filter(name__istartswith=term)
	tags = qs.order_by('name').values_list('name', flat=True).distinct()[:10]
	return JsonResponse(list(tags), safe=False)


class ShortenerListViewOpen(ListView):
	model = ShortURL
	template_name = 'shortener/shortener_list_open.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 50

	def get_queryset(self):
		qs = super().get_queryset()
		qs = qs.prefetch_related('tags').filter(private=False)
		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(Q(title__icontains=query) | Q(tags__name__icontains=query)).distinct()
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['total_results'] = paginated_total(context)
		return context


class ShortenerListByTagViewOpen(ListView):
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
		context['total_results'] = paginated_total(context)
		return context


class ShortenerAllListByTagView(LoginRequiredMixin, ListView):
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
		context['total_results'] = paginated_total(context)
		return context


class ShortenerListByTagView(OwnerListView):
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
		context['total_results'] = paginated_total(context)
		return context


class ShortenerAllByOwnerListView(LoginRequiredMixin, ListView):
	model = ShortURL
	template_name = 'shortener/shortener_list_all.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		qs = super().get_queryset()
		qs = qs.select_related('owner').prefetch_related('tags').filter(owner=self.kwargs.get('pk'))
		if str(self.request.user.pk) != str(self.kwargs.get('pk')):
			qs = qs.filter(private=False)
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Links'
		context['total_results'] = paginated_total(context)
		return context


class ShortenerByOwnerListView(OwnerListView):
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
		context['total_results'] = paginated_total(context)
		return context


class ShortenerListView(OwnerListView):
	model = ShortURL
	template_name = 'shortener/shortener_list.html'
	context_object_name = 'links'
	ordering = ['-created_at']
	paginate_by = 40

	def get_queryset(self):
		qs = super().get_queryset()
		qs = qs.select_related('owner').prefetch_related('tags')
		query = self.request.GET.get('q')
		if query:
			qs = qs.filter(Q(title__icontains=query) | Q(tags__name__icontains=query)).distinct()
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'My Links'
		context['total_results'] = paginated_total(context)
		return context


class ShortenerAllListView(LoginRequiredMixin, ListView):
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
		context['total_results'] = paginated_total(context)
		return context


class ShortenerCreateView(OwnerCreateView):
	model = ShortURL
	form_class = ShortURLForm
	template_name = 'shortener/shortener_form.html'

	def get_success_url(self):
		return reverse('shortener-detail', kwargs={'pk': self.object.pk})

	def form_valid(self, form):
		url = form.cleaned_data['long_url']

		existing = ShortURL.objects.filter(long_url=url, owner=self.request.user).first()
		if existing:
			messages.warning(self.request, "Thanks, but this link is already shortened.")
			return redirect('shortener-detail', pk=existing.pk)

		existing = ShortURL.objects.filter(long_url=url).first()
		if existing:
			messages.warning(self.request, "Thanks, but this link is already shortened.")
			if is_visible_to_user(existing, self.request.user):
				return redirect('shortener-detail-all', pk=existing.pk)
			return redirect('shortener-list')

		try:
			short_alias = generate_unique_alias()
		except RuntimeError:
			form.add_error(None, "Unable to generate a unique short link. Please try again.")
			return self.form_invalid(form)

		title = fetch_title_fast(url)

		shorturl = form.save(commit=False)
		shorturl.owner = self.request.user
		if title is not None:
			shorturl.title = title
			if title.startswith("Direct link to"):
				shorturl.private = True
		shorturl.short_alias = short_alias
		shorturl.save()
		form.save_m2m()

		if title is None:
			fetch_title_task.delay(shorturl.pk)

		self.object = shorturl
		return HttpResponseRedirect(self.get_success_url())

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Create'
		return context


class ShortenerDetailView(OwnerDetailView):
	model = ShortURL
	template_name = 'shortener/shortener_detail.html'
	context_object_name = 'link'

	def get_queryset(self):
		qs = super().get_queryset()
		return qs.select_related('owner').prefetch_related('tags')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		context['page_title'] = f"{self.object.short_alias}"
		return context


class ShortenerAllDetailView(LoginRequiredMixin, DetailView):
	model = ShortURL
	template_name = 'shortener/shortener_detail_all.html'
	context_object_name = 'link'

	def get_queryset(self):
		return visible_shorturls(self.request.user).select_related('owner').prefetch_related('tags')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page'] = self.request.GET.get('page', 1)
		context['page_title'] = f"{self.object.short_alias}"
		return context


class ShortenerUpdateView(OwnerUpdateView):
	model = ShortURL
	form_class = ShortURLUpdateForm
	template_name = 'shortener/shortener_update.html'
	context_object_name = 'link'

	def get_queryset(self):
		qs = super().get_queryset()
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
		context['page_title'] = f"Update {self.object.short_alias}"
		return context


class ShortenerAllUpdateView(OwnerUpdateView):
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
		context['page_title'] = f"Update {self.object.short_alias}"
		return context


class ShortenerDeleteView(OwnerDeleteView):
	model = ShortURL
	template_name = 'shortener/shortener_confirm_delete.html'
	context_object_name = 'link'

	def get_queryset(self):
		qs = super().get_queryset()
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
		context['page_title'] = f"Delete {self.object.short_alias}"
		return context


class ShortenerAllDeleteView(OwnerDeleteView):
	model = ShortURL
	template_name = 'shortener/shortener_confirm_delete_all.html'
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
		context['page_title'] = f"Delete {self.object.short_alias}"
		return context


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
		return ", ".join(str(tag) for tag in item.tags.all())

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
