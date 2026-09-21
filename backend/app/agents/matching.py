"""
Matching Agent (sections 5/11) — scores one job against one user's profile.
Pipeline per spec: rule-based eligibility → structured skill comparison →
semantic similarity (pgvector, optional) → LLM reasoning (optional). The LLM
never runs alone and never overrules a hard rule failure; every score ships
with persisted, human-readable reasons (FR-22/FR-23).
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.factory import get_provider
from app.models.application import Application, ApplicationStatus, StatusEvent
from app.models.job import Job
from app.models.preference import Preferences
from app.models.profile import Profile
from app.models.user import User
from app.prompts.matching import MATCH_SYSTEM_PROMPT, build_match_user_prompt
from app.services.json_repair import parse_json
from app.services.notifications import notify

logger = logging.getLogger(__name__)

CATEGORIES = {"strong", "possible", "weak", "ineligible"}


def _profile_text(profile: Profile) -> str:
    """Compact text form of the profile for embeddings / LLM prompting."""
    parts: list[str] = []
    if profile.full_name:
        parts.append(profile.full_name)
    if profile.skills:
        parts.append("Skills: " + ", ".join(s.name for s in profile.skills if s.name))
    for exp in profile.experiences:
        parts.append(f"{exp.position or 'Role'} at {exp.organization or 'n/a'}: {exp.description or ''}")
    for project in profile.projects:
        parts.append(f"Project {project.name or ''}: {project.description or ''}")
    for edu in profile.educations:
        parts.append(f"Education: {edu.degree or ''} {edu.field or ''} at {edu.institution or ''}")
    return "\n".join(part for part in parts if part.strip())[:4000]


def _cosine(a: list[float] | None, b: list[float] | None) -> float | None:
    if not a or not b or len(a) != len(b):
        return None
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return None
    return dot / (norm_a * norm_b)


def _rule_eligibility(job: Job, prefs: Preferences | None) -> list[str]:
    """Hard filters from the user's preferences. Empty list = eligible so far."""
    if prefs is None:
        return []
    failures: list[str] = []
    if prefs.work_modes and job.work_mode.value not in prefs.work_modes:
        failures.append(f"work mode {job.work_mode.value} not in preferred {prefs.work_modes}")
    if prefs.job_types and job.employment_type.value not in prefs.job_types:
        failures.append(f"employment type {job.employment_type.value} not in preferred {prefs.job_types}")
    if prefs.min_salary is not None and job.salary_max is not None and job.salary_max < prefs.min_salary:
        failures.append(f"salary max {job.salary_max} below minimum {prefs.min_salary}")
    if prefs.excluded_companies and job.company:
        excluded = {c.strip().lower() for c in prefs.excluded_companies if c}
        if job.company.strip().lower() in excluded:
            failures.append(f"company {job.company!r} is excluded")
    if prefs.excluded_roles and job.title:
        title = job.title.strip().lower()
        if any(role.strip().lower() in title for role in prefs.excluded_roles if role.strip()):
            failures.append(f"title {job.title!r} matches an excluded role")
    if prefs.preferred_locations and job.location:
        location = job.location.strip().lower()
        if not any(pref.strip().lower() in location for pref in prefs.preferred_locations if pref.strip()):
            failures.append(f"location {job.location!r} not in preferred locations")
    return failures


def _skill_overlap(job: Job, profile: Profile) -> tuple[float, list[str]]:
    """Fraction of the job's required skills the profile owns (exact match on
    lowercase names). Returns (ratio, matched skill names)."""
    required = {s.strip().lower() for s in (job.required_skills or []) if s.strip()}
    owned = {s.name.strip().lower() for s in (profile.skills or []) if s.name}
    if not required:
        return 0.0, []
    matched = sorted(required & owned)
    return len(matched) / len(required), matched


def _llm_score(job: Job, profile: Profile) -> dict | None:
    """Optional LLM reasoning step — returns None (never raises) so the
    heuristic fallback always exists."""
    try:
        provider = get_provider()
        text = provider.complete_json(
            MATCH_SYSTEM_PROMPT,
            build_match_user_prompt(
                title=job.title,
                company=job.company,
                description=job.description,
                profile_text=_profile_text(profile),
            ),
        )
        data = parse_json(text)
        try:
            score = int(float(data.get("score")))
        except (TypeError, ValueError):
            return None
        if not 0 <= score <= 100:
            return None
        category = str(data.get("category", "")).strip().lower()
        if category not in CATEGORIES:
            category = None
        reasons = [str(r).strip() for r in (data.get("reasons") or []) if str(r).strip()]
        return {"score": score, "category": category, "reasons": reasons}
    except Exception:
        logger.info("LLM matching unavailable; falling back to heuristics")
        return None


def match_job(db: Session, job: Job, user: User) -> Application:
    """Score `job` for `user`, persist score/category/reasons on the
    application row, and append the matching StatusEvent (append-only)."""
    profile = db.execute(
        select(Profile).where(Profile.user_id == user.id)
    ).scalar_one_or_none()
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    prefs = db.execute(
        select(Preferences).where(Preferences.profile_id == profile.id)
    ).scalar_one_or_none()

    reasons: list[str] = []
    failures = _rule_eligibility(job, prefs)
    skill_ratio, matched_skills = _skill_overlap(job, profile)

    similarity: float | None = None
    if job.embedding is not None:
        try:
            provider = get_provider()
            similarity = _cosine(list(job.embedding), provider.embed(_profile_text(profile)))
        except Exception:
            similarity = None

    llm = None if failures else _llm_score(job, profile)

    if failures:
        score, category = 0, "ineligible"
        reasons.extend(failures)
        reasons.append(
            f"required skills matched: {len(matched_skills)}/{len(job.required_skills or [])}"
        )
    elif llm:
        score = llm["score"]
        category = llm["category"] or ("strong" if score >= 75 else "possible" if score >= 50 else "weak")
        reasons.extend(llm["reasons"])
    else:
        sim_component = similarity if similarity is not None else 0.0
        score = round(100 * (0.6 * skill_ratio + 0.4 * sim_component))
        category = "strong" if score >= 75 else "possible" if score >= 50 else "weak"
        reasons.append(
            "heuristic score (LLM unavailable): "
            f"{skill_ratio:.0%} of required skills, "
            f"similarity {similarity if similarity is not None else 'n/a'}"
        )
    if matched_skills:
        reasons.append("matched skills: " + ", ".join(matched_skills))

    application = db.execute(
        select(Application).where(
            Application.job_id == job.id, Application.user_id == user.id
        )
    ).scalar_one_or_none()
    if application is None:
        application = Application(
            job_id=job.id,
            user_id=user.id,
            status=ApplicationStatus.discovered,
        )
        db.add(application)
        db.flush()  # assigns application.id before the first StatusEvent
        db.add(StatusEvent(
            application_id=application.id,
            status=ApplicationStatus.discovered,
            note="created by matching run",
        ))

    application.match_score = score
    application.match_category = category
    application.match_reasons = reasons[:20]

    if application.status in (ApplicationStatus.discovered, ApplicationStatus.analyzing):
        application.status = ApplicationStatus.matched
        db.add(StatusEvent(
            application_id=application.id,
            status=ApplicationStatus.matched,
            note=f"matched: score={score} category={category}",
        ))

    db.commit()
    db.refresh(application)

    if application.match_category == "strong":
        notify(
            "strong_match",
            f"Strong match ({application.match_score}/100): "
            f"{job.title or 'untitled'} at {job.company or 'unknown'}",
            "\n".join(reasons),
        )
    return application