"""Skill — categorized per section 6 (Programming languages, Frameworks, Libraries,
Databases, Cloud, AI/ML, NLP, DevOps, Testing, Other)."""
import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampedBase


class SkillCategory(str, enum.Enum):
    programming_language = "programming_language"
    framework = "framework"
    library = "library"
    database = "database"
    cloud = "cloud"
    ai_ml = "ai_ml"
    nlp = "nlp"
    devops = "devops"
    testing = "testing"
    other = "other"


class Skill(Base, TimestampedBase):
    __tablename__ = "skills"

    profile_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True
    )
    category: Mapped[SkillCategory] = mapped_column(Enum(SkillCategory), default=SkillCategory.other)
    name: Mapped[str] = mapped_column(String(100), nullable=False)