import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rendezvous.settings')
app = Celery('Rendezvous')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()