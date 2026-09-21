"""Preferences — job-matching configuration from section 6. One-to-one with Profile.
Used later by the Matching Agent (section 5/11) to filter and score jobs."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampedBase


class Preferences(Base, TimestampedBase):
    __tablename__ = "preferences"

    profile_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), unique=True, nullable=False, index=True
    )

    target_roles: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    job_types: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    internship_types: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_locations: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    work_modes: Mapped[list[str] | None] = mapped_column(ARRAY(String))  # remote / hybrid / onsite
    min_salary: Mapped[float | None] = mapped_column()
    min_stipend: Mapped[float | None] = mapped_column()
    preferred_industries: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    excluded_companies: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    excluded_roles: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    min_match_score: Mapped[int | None] = mapped_column()