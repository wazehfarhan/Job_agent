"""
Celery pipeline tasks (sections 5/27, Todo T3.1).

Beat schedule (defined in app/tasks/celery_app.py):
- daily 06:00 UTC — discover_and_extract_task (one Remotive call/day, within
  its ≤4/day and ≤2/min limits; see app/sources/remotive.py)
- hourly (minute 30) — extract_pending_sweep_task
- every 2 hours — match_sweep_task (re-match applications still `discovered`)

Tasks own their DB session (they run outside FastAPI's request scope) and
never raise into the worker — failures are logged and returned so the result
backend shows what happened.
"""
import logging

from sqlalchemy import select

from app.agents.extraction import extract_pending_jobs
from app.agents.matching import match_job
from app.core.database import SessionLocal
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.user import User
from app.services.discovery import discover_jobs
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def discover_and_extract() -> dict:
    """Daily run: pull from every enabled source, then extract what's new.

    discover_jobs() already isolates per-source failures and
    extract_pending_jobs() already isolates per-posting failures, so a single
    bad source/posting can never take down the run (NFR-7)."""
    stats: dict = {"discovered": 0, "extracted": 0, "error": None}
    db = SessionLocal()
    try:
        new_jobs = discover_jobs(db)
        stats["discovered"] = len(new_jobs)
        extracted = extract_pending_jobs(db)
        stats["extracted"] = len(extracted)
    except Exception as exc:  # defensive — the services log their own details
        logger.exception("discover_and_extract failed")
        stats["error"] = str(exc)
    finally:
        db.close()
    return stats


def extract_pending_sweep(limit: int = 50) -> dict:
    """Hourly sweep: extract postings still in `discovered` (e.g. found by an
    earlier run whose extraction step failed or was cut short)."""
    db = SessionLocal()
    try:
        extracted = extract_pending_jobs(db, limit=limit)
        return {"extracted": len(extracted)}
    except Exception as exc:
        logger.exception("extract_pending_sweep failed")
        return {"extracted": 0, "error": str(exc)}
    finally:
        db.close()


def match_sweep(limit: int = 100) -> dict:
    """Re-match applications still sitting in `discovered` (created via the
    API before any match run, or left behind by an earlier partial sweep)."""
    matched = failed = 0
    db = SessionLocal()
    try:
        applications = db.execute(
            select(Application)
            .where(Application.status == ApplicationStatus.discovered)
            .limit(limit)
        ).scalars().all()
        for application in applications:
            try:
                job = db.get(Job, application.job_id)
                user = db.get(User, application.user_id)
                if job is None or user is None:
                    continue
                match_job(db, job, user)
                matched += 1
            except Exception:
                logger.exception("match failed for application %s; skipping", application.id)
                db.rollback()  # discard partial state before the next application
                failed += 1
        return {"matched": matched, "failed": failed}
    except Exception as exc:
        logger.exception("match_sweep failed")
        db.rollback()
        return {"matched": matched, "failed": failed, "error": str(exc)}
    finally:
        db.close()


# --- Celery task wrappers (thin, so the functions stay unit-testable) ---


@celery_app.task(name="app.tasks.pipeline.discover_and_extract_task")
def discover_and_extract_task() -> dict:
    return discover_and_extract()


@celery_app.task(name="app.tasks.pipeline.extract_pending_sweep_task")
def extract_pending_sweep_task(limit: int = 50) -> dict:
    return extract_pending_sweep(limit=limit)


@celery_app.task(name="app.tasks.pipeline.match_sweep_task")
def match_sweep_task(limit: int = 100) -> dict:
    return match_sweep(limit=limit)