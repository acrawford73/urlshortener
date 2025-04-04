from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from taggit.forms import TagWidget #, TagField
from .models import ShortURL


class ShortURLForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['long_url']
		hidden_fields = ['title']


class ShortURLUpdateForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['private', 'title', 'long_url', 'tags']
		widgets = {
			'tags': TagWidget(attrs={
				'class': 'form-control',
				'id': 'tag-input',
				'multiple': 'multiple',
				'data-role': 'tagsinput'
			}),
		}
