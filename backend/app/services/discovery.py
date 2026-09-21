"""
Job Discovery — pulls jobs from every enabled JobSource, dedupes by
(source, source_job_id), and stores new rows in the jobs table.
Sections: 5 (Agent 1), 9 (deduplication + content_hash), 11 (start of the
matching pipeline). Per-source failures are logged and skipped — one broken
source must never corrupt the whole discovery run (NFR-7).
"""
import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.sources.base import JobSearchCriteria
from app.sources.registry import get_enabled_sources

logger = logging.getLogger(__name__)


def content_hash(text: str | None) -> str | None:
    """Stable hash of whitespace/lowercase-normalized text — detects posting
    changes between discovery runs (section 9)."""
    if not text or not text.strip():
        return None
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def discover_jobs(db: Session, keywords: list[str] | None = None) -> list[Job]:
    """Run every enabled source once and persist newly discovered jobs.
    Returns only the newly created rows — jobs already in the DB (matched by
    source + source_job_id) are skipped, never duplicated."""
    criteria = JobSearchCriteria(keywords=keywords or [])
    newly_created: list[Job] = []

    for source in get_enabled_sources():
        try:
            items = source.search_jobs(criteria)
        except Exception:
            logger.exception("source %s failed; skipping it for this run", source.name)
            continue

        for item in items:
            exists = db.execute(
                select(Job).where(
                    Job.source == item.source, Job.source_job_id == item.source_job_id
                )
            ).scalar_one_or_none()
            if exists is not None:
                continue

            job = Job(
                source=item.source,
                source_job_id=item.source_job_id,
                url=item.url,
                title=item.title,
                company=item.company,
                description=item.description,
                content_hash=content_hash(item.description),
            )
            db.add(job)
            newly_created.append(job)

    if newly_created:
        db.commit()
        for job in newly_created:
            db.refresh(job)

    return newly_created