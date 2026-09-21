"""
Job Extraction Agent (section 5, Agent 2) — turns a discovered posting's raw
description into structured fields on the jobs row, via the AI provider and
the json_repair validator. Never invents data: fields the model can't
confidently extract stay null/unspecified, and failures raise/log instead of
faking success (section 44).
"""
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.factory import get_provider
from app.models.job import EmploymentType, Job, JobStatus, WorkMode
from app.prompts.extraction import SYSTEM_PROMPT, build_user_prompt
from app.services.discovery import content_hash
from app.services.json_repair import parse_json
from app.sources.registry import get_source

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str | None:
    """Remotive (and most boards) return HTML descriptions; keep the text only."""
    if not text:
        return None
    return _TAG_RE.sub(" ", text).strip() or None


def _as_str(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _as_enum(value, enum_cls, default):
    try:
        return enum_cls(str(value).strip().lower())
    except (TypeError, ValueError, AttributeError):
        return default


def extract_job(db: Session, job: Job) -> Job:
    """Extract one job's structured fields. Raises ValueError for conditions
    the caller should surface as a 4xx (no adapter / no description / output
    that can't be parsed); anything else propagates as-is."""
    source = get_source(job.source)
    if source is None:
        raise ValueError(f"No adapter registered for source {job.source!r}")

    description = _strip_html(source.get_job_details(job.url))
    if not description:
        raise ValueError(f"No description available for job {job.id} from {job.source!r}")

    provider = get_provider()
    text = provider.complete_json(
        SYSTEM_PROMPT,
        build_user_prompt(title=job.title, company=job.company, description=description),
    )
    try:
        data = parse_json(text)
    except ValueError as exc:
        raise ValueError(f"Extraction output for job {job.id} could not be parsed: {exc}") from exc

    job.title = _as_str(data.get("title")) or job.title
    job.company = _as_str(data.get("company")) or job.company
    job.description = description
    job.location = _as_str(data.get("location"))
    job.work_mode = _as_enum(data.get("work_mode"), WorkMode, WorkMode.unspecified)
    job.employment_type = _as_enum(
        data.get("employment_type"), EmploymentType, EmploymentType.unspecified
    )
    job.salary_min = _as_float(data.get("salary_min"))
    job.salary_max = _as_float(data.get("salary_max"))
    job.currency = _as_str(data.get("currency"))
    job.required_skills = _as_list(data.get("required_skills"))
    job.preferred_skills = _as_list(data.get("preferred_skills"))
    job.experience_requirement = _as_str(data.get("experience_requirement"))
    job.education_requirement = _as_str(data.get("education_requirement"))
    job.deadline = _as_str(data.get("deadline"))
    job.application_url = _as_str(data.get("application_url"))
    job.content_hash = content_hash(description)
    job.status = JobStatus.extracted

    # Best-effort embedding for semantic matching (Todo T1.3) — a missing
    # embedding model must never fail the extraction itself.
    try:
        job.embedding = provider.embed(description[:4000])
    except Exception:
        logger.info("embedding unavailable for job %s; skipping", job.id)

    db.commit()
    db.refresh(job)
    return job


def extract_pending_jobs(db: Session, limit: int = 25) -> list[Job]:
    """Extract every job still in the discovered state (oldest first); failures
    are logged and skipped so one bad posting can't block the batch."""
    jobs = db.execute(
        select(Job)
        .where(Job.status == JobStatus.discovered)
        .order_by(Job.created_at.asc())
        .limit(limit)
    ).scalars().all()
    extracted: list[Job] = []
    for job in jobs:
        try:
            extracted.append(extract_job(db, job))
        except Exception:
            logger.exception("extraction failed for job %s (%s); skipping", job.id, job.url)
    return extracted
