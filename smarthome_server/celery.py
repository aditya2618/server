import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarthome_server.settings")

app = Celery("smarthome_server")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
