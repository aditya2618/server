import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarthome_server.settings")

app = Celery("smarthome_server")
app.config_from_object("django.conf:settings", namespace="CELERY")

# FORCE Redis broker (override any defaults)
app.conf.broker_url = "redis://localhost:6379/0"
app.conf.result_backend = "redis://localhost:6379/0"

app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'check-time-automations-every-minute': {
        'task': 'core.tasks_scheduler.check_time_automations',
        'schedule': crontab(minute='*'),  # Every minute
    },
}
