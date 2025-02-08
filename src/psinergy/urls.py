"""
URL configuration for project.
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings

import custom_auth.views
from django.contrib.auth import views as auth_views

# One-step registration
from django_registration.backends.one_step.views import RegistrationView
# Two-step registration
#from django_registration.backends.activation.views import RegistrationView

from custom_auth.forms import CustomRegistrationForm


urlpatterns = [

    # Admin
    #path('admin/docs/', include('django.contrib.admindocs.urls')),
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('himitsu/', admin.site.urls),

    #Apps
    path('', include('home.urls')),
    path('', include('core.urls')),
    path('', include('shortener.urls')),

    # Custom Auth
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', custom_auth.views.profile, name='profile'),
    ## The URLs supported by auth are:
    # accounts/login/ [name='login']
    # accounts/logout/ [name='logout']
  
    path('accounts/password_change/', 
         auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), 
         name='password_change'),
    path('accounts/password_change/done/', 
         auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), 
         name='password_change_done'),

    # accounts/password_change/ [name='password_change']
    # accounts/password_change/done/ [name='password_change_done']
    # accounts/password_reset/ [name='password_reset']
    #path('accounts/password_reset/', custom_auth.views.password_reset, name='password_reset'),
    # accounts/password_reset/done/ [name='password_reset_done']
    #path('accounts/password_reset/done/', custom_auth.views.password_reset_done, name='password_reset_done'),
    # accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
    # accounts/reset/done/ [name='password_reset_complete']

    # Django-Registration
    path('accounts/register/', RegistrationView.as_view(form_class=CustomRegistrationForm), name='django_registration_register'),
    # One-step registration
    path('accounts/', include('django_registration.backends.one_step.urls')),
    # Two-step registration
    #path('accounts/', include('django_registration.backends.activation.urls')),

    path('accounts/password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), 
         name='password_reset'),
    path('accounts/password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('accounts/reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
         name='password_reset_complete'),

]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
