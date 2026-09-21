"""
Celery application — broker and result backend both on REDIS_URL.

docker-compose.yml runs `celery -A app.tasks.celery_app worker` and
`celery -A app.tasks.celery_app beat` against this module. Tasks are added
under app/tasks/ and registered via include= as they exist; the beat schedule
stays empty until a scheduled task is real (Todo T3.1) — nothing is faked.
"""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "job_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[],
)

celery_app.conf.update(
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={},  # populated when scheduled tasks exist (Todo T3.1)
)