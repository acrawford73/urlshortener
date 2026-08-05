from django.test import TestCase

from shortener.utils.urls import URLValidationError, validate_url_safe


class ValidateUrlSafeTests(TestCase):
	def test_accepts_public_hostname(self):
		validate_url_safe('https://link.springer.com/article/10.1007/s12243-021-00844-0')

	def test_rejects_private_ip_hostname(self):
		with self.assertRaises(URLValidationError):
			validate_url_safe('https://192.168.1.1/')

	def test_rejects_localhost(self):
		with self.assertRaises(URLValidationError):
			validate_url_safe('https://localhost/')
