from django.db.models import Q
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import ShortURL


def visible_shorturls(user):
	qs = ShortURL.objects.all()
	if user.is_staff:
		return qs
	return qs.filter(Q(private=False) | Q(owner=user))


def is_visible_to_user(shorturl, user):
	if user.is_staff:
		return True
	if not shorturl.private:
		return True
	return shorturl.owner == user


def paginated_total(context):
	paginator = context.get('paginator')
	return paginator.count if paginator else None


class OwnerListView(LoginRequiredMixin, ListView):
	"""
	Sub-class the ListView to pass the request to the form.
	"""
	def get_queryset(self):
		qs = super(OwnerListView, self).get_queryset()
		return qs.filter(owner=self.request.user)


class OwnerDetailView(LoginRequiredMixin, DetailView):
	"""
	Sub-class the DetailView to pass the request to the form.
	"""
	def get_queryset(self):
		qs = super(OwnerDetailView, self).get_queryset()
		if self.request.user.is_staff:
			return qs
		else:
			return qs.filter(owner=self.request.user)


class OwnerCreateView(LoginRequiredMixin, CreateView):
	"""
	Sub-class of the CreateView to automatically pass the Request to the Form
	and add the owner to the saved object.
	"""

	def form_valid(self, form):
		object = form.save(commit=False)
		object.owner = self.request.user
		object.save()
		return super(OwnerCreateView, self).form_valid(form)


class OwnerUpdateView(LoginRequiredMixin, UpdateView):
	"""
	Sub-class the UpdateView to pass the request to the form and limit the
	queryset to the requesting user.
	"""

	def get_queryset(self):
		qs = super(OwnerUpdateView, self).get_queryset()
		if self.request.user.is_staff:
			return qs
		else:
			return qs.filter(owner=self.request.user)


class OwnerDeleteView(LoginRequiredMixin, DeleteView):
	"""
	Sub-class the DeleteView to restrict a User from deleting other
	user's data.
	"""

	def get_queryset(self):
		qs = super(OwnerDeleteView, self).get_queryset()
		if self.request.user.is_staff:
			return qs
		else:
			return qs.filter(owner=self.request.user)
