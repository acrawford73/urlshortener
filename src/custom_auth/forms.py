from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django_registration.forms import RegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from custom_auth.models import User
from django.core.exceptions import ValidationError


class CustomRegistrationForm(RegistrationForm):
	class Meta(RegistrationForm.Meta):
		model = User

	def __init__(self, *args, **kwargs):
		super(CustomRegistrationForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.add_input(Submit('submit', 'Register'))

	def save(self, commit=True):
		user = super().save(commit=False)
		user.is_active = False
		if commit:
			user.save()
		return user


class CustomAuthenticationForm(AuthenticationForm):
	error_messages = {
		'inactive': "The account is not active yet. Please be patient, it will be activated after review.",
		'invalid_login': "The email or password is incorrect. Please try again. The account may not be active yet.",
	}

	def confirm_login_allowed(self, user):
		if not user.is_active:
			raise ValidationError(self.error_messages['inactive'], code='inactive')

