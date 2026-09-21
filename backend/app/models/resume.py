"""
Resume — an uploaded CV file plus its parsed text (section 7).

The file itself lives on local disk under UPLOAD_DIR/<user_id>/ (see
resumes.py) — no paid cloud storage. `structured_data` is reserved for a
later AI-extraction step and stays null until that step exists; this file
only implements raw text extraction.
"""
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampedBase


class Resume(Base, TimestampedBase):
    __tablename__ = "resumes"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    label: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "AI/ML Resume"
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "pdf" | "docx"

    parsed_text: Mapped[str | None] = mapped_column(Text)
    structured_data: Mapped[str | None] = mapped_column(Text)  # JSON string; not populated yet
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)