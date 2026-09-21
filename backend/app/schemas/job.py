"""
Pydantic schemas for the job API (section 10). The structured extraction
fields (description, skills, salary, …) are included from the start so this
schema keeps working once the Extraction Agent populates them (Todo T1.1);
today only the discovery metadata is filled.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: uuid.UUID
    source: str
    source_job_id: str | None
    url: str
    company: str | None
    title: str | None
    description: str | None
    location: str | None
    work_mode: str
    employment_type: str
    salary_min: float | None
    salary_max: float | None
    currency: str | None
    required_skills: list[str] | None
    preferred_skills: list[str] | None
    deadline: str | None
    application_url: str | None
    status: str
    posted_at: str | None
    discovered_at: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class JobListOut(BaseModel):
    count: int
    jobs: list[JobOut]


class DiscoverOut(BaseModel):
    discovered: int
    jobs: list[JobOut]