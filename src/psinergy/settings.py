"""
Django settings for project.
Generated by 'django-admin startproject' using Django 4.2.
For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path
from decouple import config
from decouple import Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# ~/<virtualenv-folder>/
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: Keep the secret key used in production secret!
# SECURITY WARNING: Don't run with debug turned on in production!

if config('PRODUCTION', default=False, cast=bool) == True:
    DEBUG = False
    SECRET_KEY = config('PROD_SECRET_KEY')
    SECRET_KEY_FALLBACK = config('PROD_SECRET_KEY_FALLBACK')
    ALLOWED_HOSTS = config('PROD_ALLOWED_HOSTS', cast=Csv())
    ## Security
    SECURE_SSL_HOST = config('SECURE_SSL_HOST')
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_REFERRER_POLICY = config('SECURE_REFERRER_POLICY')
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS')
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    X_FRAME_OPTIONS = config('X_FRAME_OPTIONS')
    ## Cookies
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE')
    SESSION_COOKIE_NAME = config('SESSION_COOKIE_NAME')
    SESSION_COOKIE_DOMAIN = config('SESSION_COOKIE_DOMAIN')
    SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE')
    ## Proxy Use Only
    # SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # USE_X_FORWARDED_HOST = False
    ## E-Mail
    # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_HOST = 'email-host.com'
    # EMAIL_PORT = 587
    # EMAIL_USE_TLS = True
    # EMAIL_HOST_USER = 'email@example.com'
    # EMAIL_HOST_PASSWORD = 'email-password'
else:
    DEBUG = True
    SECRET_KEY = config('DEBUG_SECRET_KEY')
    ALLOWED_HOSTS = config('DEBUG_ALLOWED_HOSTS', cast=Csv())


### USER AUTHENTICATION

SITE_ID = int(config('SITE_ID'))
AUTH_USER_MODEL = 'custom_auth.User'
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_OPEN = False
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# Application definition

INSTALLED_APPS = [
    'custom_auth',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django.contrib.admindocs',
    'django.contrib.sites',
    'admin_honeypot',
    'crispy_forms',
    'crispy_bootstrap5',
    'shortener',
    'core',
]

ADMIN_HONEYPOT_EMAIL_ADMINS = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'psinergy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates", os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'psinergy.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'CONN_MAX_AGE': 600,
    }
}


# Password Validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


### INTERNATIONALIZATION
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = ','

### TIME ZONE
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE = 'UTC'
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

if config('PRODUCTION', default=False, cast=bool) == True:
    LOCAL_STATIC_CDN = os.path.join(os.path.dirname(BASE_DIR), 'static_cdn')
    STATIC_URL = '/static_cdn/'
else:
    LOCAL_STATIC_CDN = os.path.join(os.path.dirname(BASE_DIR), 'static_cdn')
    STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(LOCAL_STATIC_CDN, 'static')

STATICFILES_DIRS = [
   os.path.join(BASE_DIR, 'static_files')
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


### FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


### CACHING
CACHES = {
    'default': {
        #'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        #'LOCATION': 'django-local-cache',
        # /etc/memcached.conf - customize settings like memory allocation, maximum connections, and logging.
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': ['127.0.0.1:11211'],
    }
}


## Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    # 'filters': {
    #     'require_debug_false': {
    #         '()': 'django.utils.log.RequireDebugFalse',
    #     },
    # },
    'formatters': {
        'verbose': {
            #'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'filename': '/home/ubuntu/django.log',
        #     'formatter': 'verbose',
        # },
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'verbose',
        },
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'filters': ['require_debug_false'],
        # },
    },
    'loggers': {
        'django': {
            #'handlers': ['file', 'console'],
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
#    'root': {
#        #'handlers': ['file', 'console'],
#        'handlers': ['console'],
#        'level': 'INFO',
#    },
}


## Selenium
GECKO_PATH = "/usr/bin/geckodriver"
FIREFOX_PATH = "/usr/bin/firefox"

## REDIS STORE

# REDIS_LOCATION = "redis://127.0.0.1:6379/1"

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": REDIS_LOCATION,
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#     }
# }

# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
# SESSION_CACHE_ALIAS = "default"


### CELERY
# from celery.schedules import crontab

# EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
# CELERY_EMAIL_TASK_CONFIG = {
#     "queue": "short_tasks",
# }

# BROKER_URL = REDIS_LOCATION
# CELERY_RESULT_BACKEND = BROKER_URL
# CELERY_ACCEPT_CONTENT = ["application/json"]
# CELERY_TASK_SERIALIZER = "json"
# CELERY_RESULT_SERIALIZER = "json"
# CELERY_TIMEZONE = TIME_ZONE
# CELERY_SOFT_TIME_LIMIT = 2 * 60 * 60
# CELERY_WORKER_PREFETCH_MULTIPLIER = 1
# CELERYD_PREFETCH_MULTIPLIER = 1

# CELERY_BEAT_SCHEDULE = {
#     # Clear expired sessions, every sunday 1:01am 
#     # By default Django has 2 week expire date
#     "clear_sessions": {
#         "task": "clear_sessions",
#         "schedule": crontab(hour=1, minute=1, day_of_week=6),
#     },
#     "get_list_of_popular_media": {
#         "task": "get_list_of_popular_media",
#         "schedule": crontab(minute=1, hour="*/10"),
#     },
#     "update_listings_thumbnails": {
#         "task": "update_listings_thumbnails",
#         "schedule": crontab(minute=2, hour="*/30"),
#     },
# }

# CELERY_TASK_ALWAYS_EAGER = False
# if os.environ.get("TESTING"):
#     CELERY_TASK_ALWAYS_EAGER = True
