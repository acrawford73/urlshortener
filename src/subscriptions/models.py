import uuid
import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.timezone import now

stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionPlan(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=50)
	stripe_price_id = models.CharField(max_length=100)
	price = models.DecimalField(max_digits=6, decimal_places=2)
	billing_cycle = models.CharField(max_length=10, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')])

	def __str__(self):
		return f"{self.name} - {self.billing_cycle}"


class Subscription(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
	stripe_subscription_id = models.CharField(max_length=100)
	status = models.CharField(max_length=20, default='inactive')
	current_period_end = models.DateTimeField(null=True, blank=True)

	def is_active(self):
		return self.status == 'active' and self.current_period_end > now()


class Coupon(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	code = models.CharField(max_length=50, unique=True)
	discount_percent = models.IntegerField(help_text="Percentage discount")
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return f"{self.code} - {self.discount_percent}%"


class CustomDomain(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	domain = models.CharField(max_length=255, unique=True)
	short_url = models.URLField()

	def __str__(self):
		return self.domain
