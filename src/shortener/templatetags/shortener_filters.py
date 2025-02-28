from django import template

register = template.Library()


@register.filter(name='email_user')
def email_user(value):
	"""Extracts the username from email address"""
	return value.split('@')[0]
