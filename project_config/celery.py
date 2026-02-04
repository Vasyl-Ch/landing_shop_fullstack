import os
from celery import Celery

# Use unified settings for all environments
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_config.settings")

app = Celery("project_config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
