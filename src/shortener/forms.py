from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from taggit.utils import parse_tags
from .models import ShortURL
from .utils.urls import validate_url_safe, URLValidationError



class ShortURLForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['long_url']
		hidden_fields = ['title', 'private', 'tags']

	def clean_long_url(self):
		url = self.cleaned_data['long_url']
		try:
			validate_url_safe(url)
		except URLValidationError as e:
			raise forms.ValidationError(str(e))
		return url


class ShortURLUpdateForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['private', 'title', 'long_url', 'tags']

	def clean_long_url(self):
		url = self.cleaned_data['long_url']
		try:
			validate_url_safe(url)
		except URLValidationError as e:
			raise forms.ValidationError(str(e))
		return url
