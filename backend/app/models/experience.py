"""Experience — one row per job/internship the user has held (section 6)."""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampedBase


class Experience(Base, TimestampedBase):
    __tablename__ = "experiences"

    profile_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True
    )

    organization: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[str | None] = mapped_column(String(50))
    end_date: Mapped[str | None] = mapped_column(String(50))  # null/"present" = ongoing
    description: Mapped[str | None] = mapped_column(Text)
    skills_used: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    achievements: Mapped[list[str] | None] = mapped_column(ARRAY(String))