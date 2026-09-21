"""
Pydantic schemas for the resume API (section 7).

Moved here from app/services/resume.py — these are API schemas, not services,
and app/api/resumes.py imports them from app.schemas.resume.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: uuid.UUID
    label: str
    original_filename: str
    file_type: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeDetailOut(ResumeOut):
    parsed_text: str | None
    structured_data: str | None

    class Config:
        from_attributes = True