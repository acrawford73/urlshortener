from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from taggit.forms import TagWidget
from .models import ShortURL


class ShortURLForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['long_url']
		hidden_fields = ['title']


class ShortURLUpdateForm(forms.ModelForm):
	#tags = forms.CharField(widget=forms.TextInput(attrs={'id': 'tag-input', 'multiple': 'multiple'}), required=False)
	class Meta:
		model = ShortURL
		fields = ['title', 'long_url', 'tags', 'notes']
		widgets = {
			'tags': TagWidget(attrs={'class': 'form-control', 'id': 'tag-input', 'multiple': 'multiple', 'data-role': 'tagsinput'}),
		}
