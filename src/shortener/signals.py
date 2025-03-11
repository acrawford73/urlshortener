from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import ShortURL, UUIDTaggedItem
from taggit.models import Tag


@receiver(post_save, sender=ShortURL)
def clear_cache_shorturl_update(sender, instance, **kwargs):
	cache_key = f"shorturl_{instance.id}"
	cache.delete(cache_key)
	cache.set(cache_key, instance, timeout=300)  # Cache for 5 min
	cache.delete('shorturl_list')

@receiver(post_delete, sender=ShortURL)
def clear_cache_shorturl_delete(sender, instance, **kwargs):
	cache_key = f"shorturl_{instance.id}"
	cache.delete(cache_key)
	cache.delete('shorturl_list')


@receiver(post_save, post_delete, sender=UUIDTaggedItem)
def clear_cache_uuidtaggeditem(sender, instance, **kwargs):
	cache_key = f"uuidtaggeditem_{instance.id}"
	cache.delete(cache_key)
	cache.delete('uuidtaggeditem_list')
	cache.delete(f'uuidtaggeditem_{instance.id}')


@receiver(post_save, post_delete, sender=Tag)
def clear_cache_tag(sender, instance, **kwargs):
	cache_key = f"tag_{instance.id}"
	cache.delete(cache_key)
	cache.delete('tag_list')
	cache.delete(f'tag_{instance.id}')
