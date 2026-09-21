"""
Test configuration.

Sets the required env vars BEFORE any app import (app.core.config requires
SECRET_KEY/DATABASE_URL/REDIS_URL and fails fast without them), then tests
import app modules normally.

The suite is deliberately pure-unit: no database, no network, no LLM. The
ORM models use PostgreSQL-only types (UUID/ARRAY/pgvector), so DB-backed
tests need a live Postgres and are tracked separately (Todo T3.4 follow-up).
Run from backend/:  pytest
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-ci-only-not-secret")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://test:test@localhost:5432/test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AI_PROVIDER", "ollama")
os.environ.setdefault("ENV", "development")