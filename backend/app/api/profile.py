"""
GET/PUT /api/profile/me — the current user's full profile (section 6).

PUT replaces the whole set of child records (educations, skills, etc.) on
each save. For a single-user profile edited as one form, this is simpler and
harder to get wrong than diffing individual rows (see spec section 47:
prefer simple, reliable solutions).
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.experience import Experience
from app.models.preference import Preferences
from app.models.profile import Certification, Education, Profile
from app.models.project import Project
from app.models.skill import Skill, SkillCategory
from app.models.user import User
from app.schemas.profile import ProfileIn, ProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_or_create_profile(db: Session, user: User) -> Profile:
    profile = db.execute(select(Profile).where(Profile.user_id == user.id)).scalar_one_or_none()
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/me", response_model=ProfileOut)
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_or_create_profile(db, user)


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    profile = _get_or_create_profile(db, user)

    for field in (
        "full_name", "phone", "country", "city",
        "portfolio_url", "github_url", "linkedin_url", "other_links",
    ):
        setattr(profile, field, getattr(payload, field))

    db.query(Education).filter(Education.profile_id == profile.id).delete()
    db.query(Certification).filter(Certification.profile_id == profile.id).delete()
    db.query(Skill).filter(Skill.profile_id == profile.id).delete()
    db.query(Experience).filter(Experience.profile_id == profile.id).delete()
    db.query(Project).filter(Project.profile_id == profile.id).delete()
    db.query(Preferences).filter(Preferences.profile_id == profile.id).delete()

    for e in payload.educations:
        db.add(Education(profile_id=profile.id, **e.model_dump()))
    for c in payload.certifications:
        db.add(Certification(profile_id=profile.id, **c.model_dump()))
    for s in payload.skills:
        db.add(Skill(profile_id=profile.id, category=SkillCategory(s.category), name=s.name))
    for x in payload.experiences:
        db.add(Experience(profile_id=profile.id, **x.model_dump()))
    for p in payload.projects:
        db.add(Project(profile_id=profile.id, **p.model_dump()))
    if payload.preferences is not None:
        db.add(Preferences(profile_id=profile.id, **payload.preferences.model_dump()))

    db.commit()
    db.refresh(profile)
    return profile