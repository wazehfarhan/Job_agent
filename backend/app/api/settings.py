"""
GET /api/settings — non-secret runtime configuration (Todo T2.7).

Never returns secrets: no AI_API_KEY, no SECRET_KEY, no connection URLs
(they leak infrastructure topology). The frontend Settings page renders this
so the user can see which AI provider/source setup the backend is running.
"""
from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_runtime_settings(user: User = Depends(get_current_user)):
    settings = get_settings()
    return {
        "env": settings.ENV,
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": settings.AI_MODEL,
        "ai_embed_model": settings.AI_EMBED_MODEL,
        "job_source_config": settings.JOB_SOURCE_CONFIG,
        "max_upload_mb": settings.MAX_UPLOAD_MB,
        "browser_headless": settings.BROWSER_HEADLESS,
        "api_prefix": settings.API_PREFIX,
    }