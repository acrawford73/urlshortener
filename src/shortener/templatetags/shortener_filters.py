from django import template
from urllib.parse import urlparse
import tldextract


register = template.Library()


@register.filter(name='email_user')
def email_user(value):
	"""Extracts the username from email address"""
	return value.split('@')[0]


@register.filter(name='long_url_website')
def long_url_website(value):
	"""Extracts the domain from the long_url field"""
	ext = tldextract.extract(value)
	domain = f"{ext.domain}.{ext.suffix}".strip()
	return domain if ext.suffix else ext.domain.strip()
