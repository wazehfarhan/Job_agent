"""Pydantic schemas for the applications API (sections 15/16)."""
import json
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    resume_id: uuid.UUID | None = None


class TransitionIn(BaseModel):
    status: str
    note: str | None = None


class ApplicationOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    resume_id: uuid.UUID | None
    cover_letter: str | None
    match_score: int | None
    match_category: str | None
    match_reasons: list[str] = []
    created_at: datetime

    @field_validator("match_reasons", mode="before")
    @classmethod
    def _parse_reasons(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return []

    class Config:
        from_attributes = True


class StatusEventOut(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    status: str
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True