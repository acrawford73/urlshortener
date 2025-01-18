from django.contrib import admin
from .models import ShortURL


class ShortURLAdmin(admin.ModelAdmin):
	list_display = ['short_alias', 'created_at', 'clicks']
	search_fields = ['short_alias']
	class Meta:
		model = ShortURL


admin.site.register(ShortURL, ShortURLAdmin)
