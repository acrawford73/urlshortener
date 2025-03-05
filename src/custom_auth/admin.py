from django.contrib import admin
from django.contrib.sessions.models import Session
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile

import json
from django.core.cache import caches
from django.conf import settings
from django.utils.timezone import now


User = get_user_model()


from django.contrib.sessions.models import Session

class SessionAdmin(admin.ModelAdmin):
	list_display = ['session_key', '_session_data', 'expire_date']
	readonly_fields = ['_session_data']
	exclude = ['session_data']
	date_hierarchy='expire_date'
	def _session_data(self, obj):
		return obj.get_decoded()

admin.site.register(Session, SessionAdmin)


class CustomUserAdmin(UserAdmin):
	fieldsets = (
		(None, {"fields": ("email", "password")}),
		(_("Personal info"), {"fields": ("first_name", "last_name")}),
		(
			_("Permissions"),
			{
				"fields": (
				"is_active",
				"is_staff",
				"is_superuser",
				"groups",
				"user_permissions",
				)
			},
		),
		(_("Important dates"), {"fields": ("last_login", "date_joined")}),
	)
	add_fieldsets = (
		(
			None,
			{
			"classes": ("wide",),
			"fields": ("email", "password1", "password2"),
			},
		),
	)
	list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "active_sessions_count", "active_sessions")
	search_fields = ("email", "first_name", "last_name")
	ordering = ("email",)

	def active_sessions_count(self, obj):
		sessions = Session.objects.filter(expire_date__gte=now())  # Only get valid sessions
		session_count = 0
		for session in sessions:
			data = session.get_decoded()
			user_id = data.get('_auth_user_id')
			if user_id and str(user_id) == str(obj.id):  
				session_count+=1
		return str(session_count)

	def active_sessions(self, obj):
		sessions = Session.objects.filter(expire_date__gte=now())  # Only get valid sessions
		active_sessions = []

		for session in sessions:
			data = session.get_decoded()
			user_id = data.get('_auth_user_id')

			# Check if the session belongs to the user
			if user_id and str(user_id) == str(obj.id):  
				active_sessions.append(session.session_key)

	# def active_sessions(self, obj):
	# 	"""Retrieve active session keys from Redis for the user."""
	# 	session_cache = caches[settings.SESSION_CACHE_ALIAS]  # Get Redis cache
	# 	active_sessions = []

	# 	# Django session keys in Redis start with "session:"
	# 	for key in session_cache.iter_keys("*django.contrib.sessions.cache*"):  
	# 		session_data = session_cache.get(key)
	# 		if session_data:
	# 			try:
	# 				user_id = session_data.get("_auth_user_id")  # Extract user ID
	# 				if str(user_id) == str(obj.id):
	# 					active_sessions.append(key.replace(":1:django.contrib.sessions.cache", ""))
	# 			except Exception:
	# 				continue  # Ignore invalid session data

		return ", ".join(active_sessions) if active_sessions else "No active sessions"

	active_sessions_count.short_description = "Session Count"
	active_sessions.short_description = "Active Sessions"



#admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
