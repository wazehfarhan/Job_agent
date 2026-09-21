"""FastAPI application entrypoint. Run with: uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    applications,
    auth,
    jobs,
    profile,
    resumes,
    settings as settings_router,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AI Job & Internship Application Agent",
    version="0.1.0",
    description="Personal AI agent for discovering, matching, and applying to jobs/internships.",
)

app.add_middleware(
    CORSMiddleware,
    # Comma-separated via ALLOWED_ORIGINS (Todo T4.3) — no hardcoded origins.
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(jobs.router, prefix=settings.API_PREFIX)
app.include_router(profile.router, prefix=settings.API_PREFIX)
app.include_router(resumes.router, prefix=settings.API_PREFIX)
app.include_router(applications.router, prefix=settings.API_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_PREFIX)


@app.get("/api/health")
def health():
    return {"status": "ok", "env": settings.ENV}