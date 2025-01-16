from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation


class ShortURL(models.Model):
	short_alias = models.CharField(max_length=8, null=False, unique=True, editable=False)
	long_url = models.URLField(default="", null=False, blank=False)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	click_count = models.PositiveIntegerField(default=0, editable=False)
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	# def get_absolute_url(self):
	# 	return reverse('shortener-detail', kwargs={'pk': self.pk})
	class Meta:
		ordering = ['-created_at']
	def __str__(self):
		return self.short_alias
