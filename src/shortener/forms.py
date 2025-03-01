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

	# def __init__(self, *args, **kwargs):
	# 	super().__init__(*args, **kwargs)
	# 	self.helper = FormHelper()
	# 	self.helper.disable_csrf = True


class ShortURLUpdateForm(forms.ModelForm):
	class Meta:
		model = ShortURL
		fields = ['title', 'long_url', 'tags']
		widgets = {
			'tags': TagWidget(attrs={'class': 'form-control', 'id': 'tags-input', 'multiple': 'multiple', 'data-role': 'tagsinput'}),
		}
