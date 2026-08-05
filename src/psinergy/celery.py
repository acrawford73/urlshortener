from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "psinergy.settings")
app = Celery("psinergy")

# namespace='CELERY' maps CELERY_BROKER_URL -> broker_url, etc.
# Without it Celery defaults to amqp://guest@127.0.0.1:5672//
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.broker_transport_options = {"visibility_timeout": 60 * 60 * 24}
app.conf.worker_prefetch_multiplier = 1
