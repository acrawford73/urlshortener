import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation


class ShortURL(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(default="", max_length=255, null=True, blank=True)
	short_alias = models.CharField(max_length=6, null=False, unique=True, editable=False)
	long_url = models.URLField(default="", max_length=2048, null=False, blank=False, help_text="Paste in the full URL starting with HTTP or HTTPS.")
	#long_url_sha256 = models.CharField(max_length=64, default="", editable=False, unique=True) # if already exists
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	clicks = models.PositiveIntegerField(default=0, editable=False)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

	# # Open Graph
	# og_site_name = models.CharField(max_length=64, null=True, blank=True)
	# og_type = models.CharField(max_length=64, null=True, blank=True)
	# og_title = models.CharField(max_length=64, null=True, blank=True)
	# og_description = models.CharField(max_length=500, null=True, blank=True)
	# og_url = models.URLField(max_length=2048, null=True, blank=True)
	# og_image_url = models.URLField(max_length=2048, null=True, blank=True)
	# # <meta property="og:site_name" content="Website name">
	# # <meta property="og:type" content="website" />
	# # <meta property="og:title" content="Website title" />
	# # <meta property="og:description" content="Website description" />
	# # <meta property="og:url" content="https://domain.com/" />
	# # <meta property="og:image" content="https://domain.com/image.jpg" />

	# # Twits
	# tw_site = models.CharField(max_length=64, null=True, blank=True)
	# tw_title = models.CharField(max_length=64, null=True, blank=True)
	# tw_description = models.CharField(max_length=500, null=True, blank=True)
	# tw_url = models.URLField(max_length=2048, null=True, blank=True)
	# tw_image_url = models.URLField(max_length=2048, null=True, blank=True)
	# tw_image_alt = models.CharField(max_length=500, null=True, blank=True)
	# # <meta name="twitter:title" content="Website title" />
	# # <meta name="twitter:description" content="Website description" />
	# # <meta name="twitter:image" content="https://domain.com/image.jpg" />
	# # <meta name="twitter:image:alt" content="Alt text for image">

	def get_absolute_url(self):
		return reverse('shortener-list')
	class Meta:
		ordering = ['-created_at']
	def __str__(self):
		return f"{self.short_alias} -> {self.long_url}"

