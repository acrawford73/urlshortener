from django import template
from urllib.parse import urlparse

register = template.Library()


@register.filter(name='email_user')
def email_user(value):
	"""Extracts the username from email address"""
	return value.split('@')[0]

@register.filter(name='long_url_website')
def long_url_website(value):
	"""Extracts the domain from the long_url field"""
	domain = urlparse(value).netloc
	if domain.startswith('www.'):
		return domain.replace('www.', '')
	return '.'.join(domain.split('.')[-2:])