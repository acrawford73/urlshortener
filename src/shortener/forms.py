from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from .models import ShortURL


class ShortURLForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['long_url']
		hidden_fields = ['title']
