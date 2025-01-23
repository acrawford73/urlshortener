from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from .models import ShortURL

# class ShortURLForm(forms.Form):
# 	long_url = forms.URLField()

# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
# 		self.helper = FormHelper()
# 		self.helper.layout = Layout(
# 			Field('long_url', wrapper_class='form-group', label="Long URL")
# 		)

class ShortURLForm(forms.ModelForm):
    class Meta:
        model = ShortURL
        fields = ['Long_url']
