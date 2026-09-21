"""Prompt templates for the Job Extraction Agent (section 5, Agent 2)."""

SYSTEM_PROMPT = """You extract structured data from job postings.
Return ONLY a single JSON object — no markdown fences, no commentary — with
exactly these keys:
{"title": str|null, "company": str|null, "location": str|null,
 "work_mode": "remote"|"hybrid"|"onsite"|"unspecified",
 "employment_type": "internship"|"full_time"|"part_time"|"contract"|"unspecified",
 "salary_min": number|null, "salary_max": number|null, "currency": str|null,
 "required_skills": [str], "preferred_skills": [str],
 "experience_requirement": str|null, "education_requirement": str|null,
 "deadline": str|null (ISO date when stated), "application_url": str|null}

Use null/[] whenever a field is not stated in the posting. NEVER invent
values — only restate what the posting actually says."""


def build_user_prompt(*, title: str | None, company: str | None, description: str) -> str:
    return f"""Extract the structured fields from this job posting.

Known from discovery (correct them ONLY if the description contradicts them):
Title: {title or "unknown"}
Company: {company or "unknown"}

Posting content:
{description[:8000]}"""
