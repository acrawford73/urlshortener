from django.contrib import admin
from .models import ShortURL


class ShortURLAdmin(admin.ModelAdmin):
	list_display = ['short_alias', 'clicks', 'title', 'owner', 'created_at']
	search_fields = ['title', 'short_alias']
	
	class Meta:
		model = ShortURL


admin.site.register(ShortURL, ShortURLAdmin)
