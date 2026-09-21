"""
Celery application — broker and result backend both on REDIS_URL.

docker-compose.yml runs `celery -A app.tasks.celery_app worker` and
`celery -A app.tasks.celery_app beat` against this module. Pipeline tasks
live in app/tasks/pipeline.py; the beat schedule below automates the
discovery → extraction → matching sweeps (Todo T3.1).
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "job_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.pipeline"],
)

celery_app.conf.update(
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        # One Remotive call/day — well inside its ≤4/day, ≤2/min limits.
        "daily-discovery-and-extraction": {
            "task": "app.tasks.pipeline.discover_and_extract_task",
            "schedule": crontab(hour=6, minute=0),
        },
        # Catch postings whose extraction failed or was cut short.
        "hourly-extraction-sweep": {
            "task": "app.tasks.pipeline.extract_pending_sweep_task",
            "schedule": crontab(minute=30),
        },
        # Re-match applications still sitting in `discovered`.
        "matching-sweep": {
            "task": "app.tasks.pipeline.match_sweep_task",
            "schedule": crontab(hour="*/2", minute=0),
        },
    },
)