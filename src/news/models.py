import uuid
from django.db import models
from django.db.models import Index
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation



class News(models.Model):
	"""News Items"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(default="", max_length=500, null=False, blank=False)
	content = models.TextField(default="", max_length=2000, null=True, blank=True)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	created = models.DateTimeField(auto_now_add=True, editable=False)
	updated = models.DateTimeField(auto_now=True, editable=False)

	def get_absolute_url(self):
		return reverse('news-list')

	class Meta:
		ordering = ['-created']
		indexes = [
			Index(fields=['title']),
			Index(fields=['-created']),
		]
	def __str__(self):
		return self.title

