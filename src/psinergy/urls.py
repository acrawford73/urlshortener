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

import core.views
import custom_auth.views
import shortener.views

from django_registration.backends.activation.views import RegistrationView
from custom_auth.forms import CustomRegistrationForm


urlpatterns = [

    # Admin
    path('admin/docs/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),

    #Apps
    path('', include('shortener.urls')),
    path('', include('core.urls')),

    # Custom Auth
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', custom_auth.views.profile, name='profile'),
    ## The URLs supported by auth are:
    # accounts/login/ [name='login']
    # accounts/logout/ [name='logout']
    # accounts/password_change/ [name='password_change']
    # accounts/password_change/done/ [name='password_change_done']
    # accounts/password_reset/ [name='password_reset']
    # accounts/password_reset/done/ [name='password_reset_done']
    # accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
    # accounts/reset/done/ [name='password_reset_complete']

    # Django-Registration
    #path('user/register/', RegistrationView.as_view(form_class=CustomRegistrationForm), name='django_registration_register'),
    path('user/', include('django_registration.backends.activation.urls')),

]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
