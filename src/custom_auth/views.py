from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, PasswordResetConfirmView, PasswordResetDoneView
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic.edit import FormView

from django.contrib.auth import get_user_model
from django_registration.backends.one_step.views import RegistrationView

from shortener.models import ShortURL
from shortener.utils.throttle import check_rate_limit

from .forms import CustomAuthenticationForm


User = get_user_model()

PASSWORD_RESET_RATE = 5
PASSWORD_RESET_WINDOW = 60 * 60


class CustomPasswordResetView(FormView):
	template_name = 'registration/password_reset_form.html'
	form_class = PasswordResetForm

	def post(self, request, *args, **kwargs):
		if not check_rate_limit(request, 'throttle:password_reset', PASSWORD_RESET_RATE, PASSWORD_RESET_WINDOW):
			return HttpResponse("Rate limit exceeded. Please try again later.", status=429)

		form = self.get_form()
		if not form.is_valid():
			return self.form_invalid(form)

		email = form.cleaned_data['email']
		user = User.objects.filter(email=email).first()
		context = {'page_title': 'Password Reset Link'}

		if user:
			uid = urlsafe_base64_encode(force_bytes(user.pk))
			token = default_token_generator.make_token(user)
			context['reset_link'] = request.build_absolute_uri(
				reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
			)

		response = render(request, 'registration/password_reset_link.html', context)
		response['Cache-Control'] = 'no-store'
		return response

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Password Reset'
		return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
	template_name = 'registration/password_reset_confirm.html'
	success_url = reverse_lazy('password_reset_complete')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Password Reset Confirm'
		return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
	"""
	This view is never actually used in this case, but we override it to prevent redirection.
	"""
	def get(self, request, *args, **kwargs):
		return render(request, 'registration/password_reset_link.html')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Password Reset Link'
		return context


class CustomRegistrationView(RegistrationView):
	def register(self, form):
		user = form.save()
		return user

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Register'
		return context


class CustomLoginView(LoginView):
	authentication_form = CustomAuthenticationForm

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Login'
		return context


@login_required
def profile(request):
	shorturl_count = ShortURL.objects.filter(owner=request.user).count()
	return render(request, 'custom_auth/profile.html', {'page_title': 'Profile', 'shorturl_count': shorturl_count})


@login_required
def password_change(request):
	return render(request, 'custom_auth/password_change_form.html', {'page_title': 'Password Change'})


@login_required
def password_change_done(request):
	return render(request, 'custom_auth/password_change_done.html', {'page_title': 'Password Change Complete'})
