from django.urls import path
import uuid
from . import views


urlpatterns = [

	# path('list/',					views.SubscriptionListView.as_view(), 		name='subscription-list'),
	# path('create/', 				views.CreateCheckoutSessionView.as_view(), 	name='checkout-create'),
	# path('sub-hook/', 				views.SubscriptionWebhookView.as_view(), 	name='subscription-hook'),
	# path('delete/<uuid:pk>/',		views.ShortenerDeleteView.as_view(), 	name='shortener-delete'),
	# path('detail/<uuid:pk>/', 		views.ShortenerDetailView.as_view(), 	name='shortener-detail'),

	path('checkout/', 				CreateCheckoutSessionView.as_view(), 	name='create-checkout-session'),
	path('webhook/', 				SubscriptionWebhookView.as_view(), 		name='subscription-webhook'),
	path('subscription/<uuid:pk>/', SubscriptionDetailView.as_view(),		name='subscription-detail'),
	path('success/', 				SubscriptionSuccessView.as_view(), 		name='subscription_success'),
	path('cancel/', 				SubscriptionCancelView.as_view(), 		name='subscription-cancel'),
	path('cancel/<uuid:pk>/', 		CancelSubscriptionView.as_view(), 		name='cancel-subscription'),
	
]