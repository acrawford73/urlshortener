from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from taggit.forms import TagWidget
from taggit.utils import parse_tags
from .models import ShortURL



class ShortURLForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['long_url']
		hidden_fields = ['title', 'private', 'tags']


class ShortURLUpdateForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['private', 'title', 'long_url', 'tags']
