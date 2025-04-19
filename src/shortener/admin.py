from django.contrib import admin
from .models import ShortURL


class ShortURLAdmin(admin.ModelAdmin):
	list_display = ['short_alias', 'title', 'owner', 'private', 'created_at']
	search_fields = ['title', 'short_alias']
	fields = ['private', 'title', 'long_url', 'owner', 'notes']

	class Meta:
		model = ShortURL


admin.site.register(ShortURL, ShortURLAdmin)
