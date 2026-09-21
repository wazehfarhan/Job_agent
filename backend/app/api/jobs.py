"""GET /api/jobs — list discovered jobs. POST /api/jobs/discover — pull new jobs from enabled sources."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.job import Job
from app.models.user import User
from app.schemas.job import DiscoverOut, JobListOut, JobOut
from app.services.discovery import discover_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListOut)
def list_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    jobs = db.execute(
        select(Job).order_by(Job.discovered_at.desc()).limit(limit).offset(offset)
    ).scalars().all()
    return {"count": len(jobs), "jobs": jobs}


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/discover", response_model=DiscoverOut)
def trigger_discovery(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Manually trigger job discovery across all enabled sources (section 5,
    Agent 1). Scheduled/automatic discovery is added in a later step (section 27)."""
    new_jobs = discover_jobs(db)
    return {"discovered": len(new_jobs), "jobs": new_jobs}