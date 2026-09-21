"""Shared Redis client (used for caching, rate limiting, and as the Celery broker/backend)."""
import redis

from app.core.config import get_settings

settings = get_settings()

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)