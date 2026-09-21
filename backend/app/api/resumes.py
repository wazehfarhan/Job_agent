"""
Resume upload, listing, retrieval, and deletion (section 7).

Files are stored on local disk under UPLOAD_DIR/<user_id>/ — no paid cloud
storage. Only PDF and DOCX are accepted; size is capped by MAX_UPLOAD_MB
(section 24: file type validation, max upload size). Stored filenames are
random UUIDs, never the user-supplied name, to avoid path traversal /
collisions; the original name is kept only as display metadata.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeDetailOut, ResumeOut
from app.services.resume_parser import extract_text

router = APIRouter(prefix="/resumes", tags=["resumes"])
settings = get_settings()

ALLOWED_EXTENSIONS = {"pdf": "pdf", "docx": "docx"}


def _resolve_file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX resumes are supported",
        )
    return ALLOWED_EXTENSIONS[ext]


@router.post("", response_model=ResumeDetailOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    label: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_type = _resolve_file_type(file.filename)

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_MB}MB limit",
        )

    user_dir = Path(settings.UPLOAD_DIR) / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}.{file_type}"
    file_path = user_dir / stored_filename
    file_path.write_bytes(contents)

    try:
        parsed_text = extract_text(str(file_path), file_type)
    except Exception:
        # Extraction failed (e.g. scanned/image-only PDF) — the file is
        # still stored; parsed_text stays null rather than guessing content.
        parsed_text = None

    resume = Resume(
        user_id=user.id,
        label=label,
        original_filename=file.filename,
        file_path=str(file_path),
        file_type=file_type,
        parsed_text=parsed_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
    ).scalars().all()


@router.get("/{resume_id}", response_model=ResumeDetailOut)
def get_resume(resume_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.put("/{resume_id}/set-default", response_model=ResumeOut)
def set_default_resume(
    resume_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    db.query(Resume).filter(Resume.user_id == user.id, Resume.id != resume.id).update(
        {"is_default": False}, synchronize_session=False
    )
    resume.is_default = True
    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    Path(resume.file_path).unlink(missing_ok=True)
    db.delete(resume)
    db.commit()