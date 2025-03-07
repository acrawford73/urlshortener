import uuid
from django.db import models
from django.db.models import Index
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase


class ShortURL(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(default="", max_length=500, null=True, blank=True)
	short_alias = models.CharField(max_length=6, null=False, unique=True, editable=False)
	long_url = models.URLField(default="", max_length=2048, null=False, blank=False, \
		help_text="Place the full URL starting with https://")
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	clicks = models.PositiveIntegerField(default=0, editable=False)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	tags = TaggableManager(through='UUIDTaggedItem', blank=True)
	notes = models.TextField(default="", max_length=500, blank=True, \
		help_text="Additional info up to 500 characters.")

	def get_absolute_url(self):
		return reverse('shortener-list')

	class Meta:
		ordering = ['-created_at']
		indexes = [
			Index(fields=['short_alias']),
			Index(fields=['-created_at']),
		]
	def __str__(self):
		return self.short_alias


# Custom Through Model for Taggit
class UUIDTaggedItem(TaggedItemBase):
	content_object = models.ForeignKey(ShortURL, on_delete=models.CASCADE, related_name="tagged_items")
