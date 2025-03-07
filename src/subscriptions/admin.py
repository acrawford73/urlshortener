from django.contrib import admin
from .models import Subscription, SubscriptionPlan, Coupon, CustomDomain


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
	list_display = ("name", "price", "billing_cycle")

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
	list_display = ("code", "discount_percent", "is_active")
	list_filter = ("is_active",)
	search_fields = ("code",)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
	list_display = ("user", "plan", "status", "current_period_end")
	list_filter = ("status",)
	search_fields = ("user__email")

@admin.register(CustomDomain)
class CustomDomainAdmin(admin.ModelAdmin):
	list_display = ("user", "domain", "short_url")
	search_fields = ("domain",)


# admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
# admin.site.register(Subscription, SubscriptionAdmin)
# admin.site.register(Coupon, CouponAdmin)
# admin.site.register(CustomDomain, CustomDomainAdmin)
