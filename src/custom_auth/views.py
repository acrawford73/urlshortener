from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy

from django.views.generic.edit import FormView
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView

from django_registration.backends.one_step.views import RegistrationView
from django.contrib.auth import login

from .forms import CustomAuthenticationForm


@login_required
def profile(request):
	return render(request, 'custom_auth/profile.html')

@login_required
def password_change(request):
	return render(request, 'custom_auth/password_change_form.html')

@login_required
def password_change_done(request):
	return render(request, 'custom_auth/password_change_done.html')


User = get_user_model()

class CustomPasswordResetView(FormView):
	template_name = 'registration/password_reset_form.html'
	form_class = PasswordResetForm

	def post(self, request, *args, **kwargs):
		form = self.get_form()
		if form.is_valid():
			email = form.cleaned_data['email']
			user = User.objects.filter(email=email).first()
			if user:
				uid = urlsafe_base64_encode(force_bytes(user.pk))
				token = default_token_generator.make_token(user)
				reset_link = request.build_absolute_uri(
					reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
				)
			return render(request, 'registration/password_reset_link.html', {'reset_link': reset_link})
		return render(request, 'registration/password_reset_done.html')  # If email not found, let them think it worked


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'  # Use your custom template
    success_url = reverse_lazy('password_reset_done')  # Redirect after successful reset


class CustomPasswordResetDoneView(PasswordResetDoneView):
	"""
	This view is never actually used in this case, but we override it to prevent redirection.
	"""
	def get(self, request, *args, **kwargs):
		return render(request, 'registration/password_reset_link.html')


class CustomRegistrationView(RegistrationView):
	def register(self, form):
		user = form.save()
		# Prevent auto-login
		return user


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm

