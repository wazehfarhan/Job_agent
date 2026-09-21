"""Re-export every model so `from app.models import X` works and Alembic's
Base.metadata stays fully populated (alembic/env.py imports the submodules
directly; this file is the convenience layer)."""
from app.models.application import Application, ApplicationStatus, StatusEvent
from app.models.base import TimestampedBase
from app.models.experience import Experience
from app.models.job import EmploymentType, Job, JobStatus, WorkMode
from app.models.preference import Preferences
from app.models.profile import Certification, Education, Profile
from app.models.project import Project
from app.models.resume import Resume
from app.models.skill import Skill, SkillCategory
from app.models.user import User

__all__ = [
    "Application", "ApplicationStatus", "StatusEvent", "TimestampedBase",
    "Experience", "EmploymentType", "Job", "JobStatus", "WorkMode",
    "Preferences", "Certification", "Education", "Profile", "Project",
    "Resume", "Skill", "SkillCategory", "User",
]
