"""
Job model — one row per discovered posting (see spec section 10).

`content_hash` + `source`/`source_job_id` are what deduplication (section 9)
keys off of; the matching pipeline (section 11) reads the structured fields
populated by the Job Extraction Agent. `embedding` is the pgvector column for
semantic matching (Todo T1.3).
"""
import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Enum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampedBase


class WorkMode(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    unspecified = "unspecified"


class EmploymentType(str, enum.Enum):
    internship = "internship"
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    unspecified = "unspecified"


class JobStatus(str, enum.Enum):
    """Lifecycle of a discovered posting (distinct from ApplicationStatus)."""
    discovered = "discovered"
    extracted = "extracted"
    duplicate = "duplicate"
    matched = "matched"
    ineligible = "ineligible"
    expired = "expired"


class Job(Base, TimestampedBase):
    __tablename__ = "jobs"

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_job_id: Mapped[str | None] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    company: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)

    location: Mapped[str | None] = mapped_column(String(255))
    work_mode: Mapped[WorkMode] = mapped_column(Enum(WorkMode), default=WorkMode.unspecified)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType), default=EmploymentType.unspecified
    )

    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(10))

    required_skills: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_skills: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    experience_requirement: Mapped[str | None] = mapped_column(Text)
    education_requirement: Mapped[str | None] = mapped_column(Text)

    deadline: Mapped[str | None] = mapped_column(String(50))  # normalized to ISO date once parsed
    application_url: Mapped[str | None] = mapped_column(Text)

    posted_at: Mapped[str | None] = mapped_column(String(50))
    discovered_at: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.discovered, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    # Semantic matching (Todo T1.3). 768 dims = nomic-embed-text (AI_EMBED_MODEL);
    # change the migration, this column, and the config together.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)