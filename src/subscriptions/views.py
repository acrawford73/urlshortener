import stripe
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Subscription, SubscriptionPlan, Coupon, CustomDomain
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

User = get_user_model()


class SubscriptionSuccessView(LoginRequiredMixin, View):
    """Subscription successful view."""
    model = Subscription
    def get(self, request, *args, **kwargs):
        return render(request, 'subscriptions/subscriptions_success.html')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Subscription Successful'
        return context


class SubscriptionDetailView(LoginRequiredMixin, View):
    """Details for a specific subscription."""
    model = Subscription
    def get(self, request, *args, **kwargs):
        subscription = Subscription.objects.filter(user=request.user).first()
        return render(request, 'subscriptions/subscriptions_detail.html', {'subscription': subscription})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Subscription'
        return context


class SubscriptionCancelView(LoginRequiredMixin, View):
    """Subscription cancel view."""
    model = Subscription
    def get(self, request, *args, **kwargs):
        return render(request, 'subscriptions/subscriptions_cancel.html')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Subscription Cancel'
        return context


class CancelSubscriptionView(LoginRequiredMixin, View):
    """Cancels the subscription."""
    model = Subscription
    def post(self, request, *args, **kwargs):
        subscription = Subscription.objects.get(user=request.user)
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        subscription.status = 'canceled'
        subscription.save()
        return redirect('subscription-detail')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Subscription Cancel'
        return context


class CreateCheckoutSessionView(LoginRequiredMixin, View):
    """User begins checkout process."""
    def post(self, request, *args, **kwargs):
        plan_id = request.POST.get('plan_id')
        coupon_code = request.POST.get('coupon')
        
        plan = SubscriptionPlan.objects.get(id=plan_id)
        stripe_session_data = {
            'payment_method_types': ['card'],
            'mode': 'subscription',
            'line_items': [{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            'success_url': request.build_absolute_uri(reverse('subscription-success')),
            'cancel_url': request.build_absolute_uri(reverse('subscription-cancel')),
        }

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                stripe_coupon = stripe.Coupon.create(
                    percent_off=coupon.discount_percent,
                    duration='once'
                )
                stripe_session_data['discounts'] = [{'coupon': stripe_coupon.id}]
            except Coupon.DoesNotExist:
                pass

        checkout_session = stripe.checkout.Session.create(**stripe_session_data)
        return JsonResponse({'sessionId': checkout_session.id})


class SubscriptionWebhookView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return JsonResponse({'status': 'error'}, status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user = User.objects.get(email=session['customer_email'])
            subscription = stripe.Subscription.retrieve(session['subscription'])
            plan = SubscriptionPlan.objects.get(stripe_price_id=subscription['items']['data'][0]['price']['id'])
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'stripe_subscription_id': subscription.id,
                    'status': subscription.status,
                    'current_period_end': subscription['current_period_end']
                }
            )

        return JsonResponse({'status': 'success'})


class CustomDomainRedirectView(View):
    """Redirect for subscriber's custom domains"""
    def get(self, request, domain, *args, **kwargs):
        custom_domain = get_object_or_404(CustomDomain, domain=domain)
        return HttpResponseRedirect(custom_domain.short_url)

