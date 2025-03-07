from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
# Models
from .models import ShortURL, UUIDTaggedItem
from taggit.models import Tag


@receiver(post_save, sender=ShortURL)
@receiver(post_delete, sender=ShortURL)
def clear_cache_shorturl(sender, instance, **kwargs):
	cache_key = f"shorturl_{instance.id}"
	# cache.set(cache_key, instance, timeout=300)  # Cache for 5 min
	cache.delete(cache_key)
	cache.delete('shorturl_list')
	cache.delete(f'shorturl_{instance.id}')


@receiver(post_save, sender=UUIDTaggedItem)
@receiver(post_delete, sender=UUIDTaggedItem)
def clear_cache_uuidtaggeditem(sender, instance, **kwargs):
	cache_key = f"uuidtaggeditem_{instance.id}"
	cache.delete(cache_key)
	cache.delete('uuidtaggeditem_list')
	cache.delete(f'uuidtaggeditem_{instance.id}')


@receiver(post_save, sender=Tag)
@receiver(post_delete, sender=Tag)
def clear_cache_tag(sender, instance, **kwargs):
	cache_key = f"tag_{instance.id}"
	cache.delete(cache_key)
	cache.delete('tag_list')
	cache.delete(f'tag_{instance.id}')
