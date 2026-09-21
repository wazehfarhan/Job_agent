"""Profile — personal info (section 6). One-to-one with User. Education and
Certification are one-to-many child tables owned by a Profile."""
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampedBase


class Profile(Base, TimestampedBase):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    other_links: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    educations: Mapped[list["Education"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    skills: Mapped[list["Skill"]] = relationship(cascade="all, delete-orphan")
    experiences: Mapped[list["Experience"]] = relationship(cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(cascade="all, delete-orphan")
    preferences: Mapped["Preferences | None"] = relationship(
        cascade="all, delete-orphan", uselist=False
    )


class Education(Base, TimestampedBase):
    __tablename__ = "educations"

    profile_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True
    )

    institution: Mapped[str | None] = mapped_column(String(255))
    degree: Mapped[str | None] = mapped_column(String(255))
    field: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[str | None] = mapped_column(String(50))
    expected_graduation: Mapped[str | None] = mapped_column(String(50))
    gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))  # optional — user chooses whether to provide it

    profile: Mapped["Profile"] = relationship(back_populates="educations")


class Certification(Base, TimestampedBase):
    __tablename__ = "certifications"

    profile_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True
    )

    name: Mapped[str | None] = mapped_column(String(255))
    issuer: Mapped[str | None] = mapped_column(String(255))
    date: Mapped[str | None] = mapped_column(String(50))
    credential_url: Mapped[str | None] = mapped_column(String(500))

    profile: Mapped["Profile"] = relationship(back_populates="certifications")