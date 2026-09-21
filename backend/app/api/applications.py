"""
Applications API — one row per job application attempt (sections 15/16).

Every status change goes through POST /{id}/transition, which APPENDS a
status_events row (section 16: history is never mutated in place). The
Matching Agent's results (score/category/reasons) land on the same row via
POST /{id}/match.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.matching import match_job
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.application import Application, ApplicationStatus, StatusEvent
from app.models.job import Job
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationOut,
    StatusEventOut,
    TransitionIn,
)
from app.services.notifications import notify

router = APIRouter(prefix="/applications", tags=["applications"])


def _owned_or_404(db: Session, user: User, application_id: str) -> Application:
    application = db.get(Application, application_id)
    if application is None or application.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@router.get("", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.execute(
        select(Application)
        .where(Application.user_id == user.id)
        .order_by(Application.created_at.desc())
    ).scalars().all()


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = db.get(Job, payload.job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing = db.execute(
        select(Application).where(
            Application.job_id == job.id, Application.user_id == user.id
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application already exists for this job",
        )

    application = Application(
        job_id=job.id,
        user_id=user.id,
        resume_id=payload.resume_id,
        status=ApplicationStatus.discovered,
    )
    db.add(application)
    db.flush()  # assigns application.id before the first StatusEvent
    db.add(StatusEvent(
        application_id=application.id,
        status=ApplicationStatus.discovered,
        note="application created",
    ))
    db.commit()
    db.refresh(application)
    return application


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _owned_or_404(db, user, application_id)


@router.get("/{application_id}/events", response_model=list[StatusEventOut])
def list_events(
    application_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = _owned_or_404(db, user, application_id)
    return db.execute(
        select(StatusEvent)
        .where(StatusEvent.application_id == application.id)
        .order_by(StatusEvent.created_at.asc())
    ).scalars().all()


@router.post("/{application_id}/transition", response_model=ApplicationOut)
def transition(
    application_id: str,
    payload: TransitionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = _owned_or_404(db, user, application_id)
    try:
        new_status = ApplicationStatus(payload.status)
    except ValueError:
        valid = [s.value for s in ApplicationStatus]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid status {payload.status!r}; valid values: {valid}",
        )
    application.status = new_status
    db.add(StatusEvent(
        application_id=application.id,
        status=new_status,
        note=payload.note,
    ))
    db.commit()
    db.refresh(application)
    notify(
        "status_change",
        f"Application {application.id} → {new_status.value}",
        payload.note or "",
    )
    return application


@router.post("/{application_id}/match", response_model=ApplicationOut)
def match_application(
    application_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Run the Matching Agent for this application's job (section 11)."""
    application = _owned_or_404(db, user, application_id)
    job = db.get(Job, application.job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return match_job(db, job, user)