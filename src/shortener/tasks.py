from celery import shared_task

from shortener.models import ShortURL
from shortener.utils.titles import fetch_title_full


@shared_task(soft_time_limit=120)
def fetch_title_task(shorturl_id):
	shorturl = ShortURL.objects.get(pk=shorturl_id)
	title = fetch_title_full(shorturl.long_url)
	if title:
		updates = {'title': title}
		if title.startswith("Direct link to"):
			updates['private'] = True
		ShortURL.objects.filter(pk=shorturl_id).update(**updates)
