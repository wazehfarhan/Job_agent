"""Pydantic schemas for the profile API — mirrors section 6 of the spec."""
import uuid

from pydantic import BaseModel


class EducationIn(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    expected_graduation: str | None = None
    gpa: float | None = None


class EducationOut(EducationIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class CertificationIn(BaseModel):
    name: str | None = None
    issuer: str | None = None
    date: str | None = None
    credential_url: str | None = None


class CertificationOut(CertificationIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class SkillIn(BaseModel):
    category: str = "other"
    name: str


class SkillOut(SkillIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class ExperienceIn(BaseModel):
    organization: str | None = None
    position: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    skills_used: list[str] = []
    achievements: list[str] = []


class ExperienceOut(ExperienceIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class ProjectIn(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = []
    url: str | None = None
    github_url: str | None = None
    responsibilities: list[str] = []
    achievements: list[str] = []


class ProjectOut(ProjectIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class PreferencesIn(BaseModel):
    target_roles: list[str] = []
    job_types: list[str] = []
    internship_types: list[str] = []
    preferred_locations: list[str] = []
    work_modes: list[str] = []
    min_salary: float | None = None
    min_stipend: float | None = None
    preferred_industries: list[str] = []
    keywords: list[str] = []
    excluded_companies: list[str] = []
    excluded_roles: list[str] = []
    min_match_score: int | None = None


class PreferencesOut(PreferencesIn):
    class Config:
        from_attributes = True


class ProfileIn(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    portfolio_url: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    other_links: list[str] = []

    educations: list[EducationIn] = []
    certifications: list[CertificationIn] = []
    skills: list[SkillIn] = []
    experiences: list[ExperienceIn] = []
    projects: list[ProjectIn] = []
    preferences: PreferencesIn | None = None


class ProfileOut(BaseModel):
    id: uuid.UUID
    full_name: str | None
    phone: str | None
    country: str | None
    city: str | None
    portfolio_url: str | None
    github_url: str | None
    linkedin_url: str | None
    other_links: list[str] | None

    educations: list[EducationOut] = []
    certifications: list[CertificationOut] = []
    skills: list[SkillOut] = []
    experiences: list[ExperienceOut] = []
    projects: list[ProjectOut] = []
    preferences: PreferencesOut | None = None

    class Config:
        from_attributes = True