"""Project — one row per project the user lists (section 6)."""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampedBase


class Project(Base, TimestampedBase):
    __tablename__ = "projects"

    profile_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True
    )

    name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    technologies: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    responsibilities: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    achievements: Mapped[list[str] | None] = mapped_column(ARRAY(String))