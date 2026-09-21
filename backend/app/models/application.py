"""
Application model — tracks one job application from prep through outcome.

ApplicationStatus enumerates the lifecycle from spec section 15.
StatusEvent gives the append-only timeline required by section 16 — never
mutate history in place, always append a new event.
"""
import enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampedBase


class ApplicationStatus(str, enum.Enum):
    discovered = "discovered"
    analyzing = "analyzing"
    matched = "matched"
    preparing = "preparing"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    submitting = "submitting"
    applied = "applied"
    interview = "interview"
    rejected = "rejected"
    withdrawn = "withdrawn"
    failed = "failed"
    needs_user_action = "needs_user_action"


class Application(Base, TimestampedBase):
    __tablename__ = "applications"

    job_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        default=ApplicationStatus.discovered, index=True
    )

    resume_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"))
    cover_letter: Mapped[str | None] = mapped_column(Text)
    answers_json: Mapped[str | None] = mapped_column(Text)  # serialized Q&A, validated via Pydantic at the API layer

    match_score: Mapped[int | None] = mapped_column()
    match_category: Mapped[str | None] = mapped_column(String(20))  # strong | possible | weak | ineligible


class StatusEvent(Base, TimestampedBase):
    """Append-only timeline entry — one row per status transition (section 16)."""
    __tablename__ = "status_events"

    application_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    status: Mapped[ApplicationStatus] = mapped_column(nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
