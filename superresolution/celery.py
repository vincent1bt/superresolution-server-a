import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superresolution.settings.development')

app = Celery('superresolution')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()