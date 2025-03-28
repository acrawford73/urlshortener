from django.contrib import admin
from .models import News


class NewsAdmin(admin.ModelAdmin):
	list_display = ['title', 'created', 'updated']
	search_fields = ['title']
	
	class Meta:
		model = News


admin.site.register(News, NewsAdmin)
