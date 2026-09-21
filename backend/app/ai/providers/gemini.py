"""
Gemini provider — free tier, called via the REST API with httpx (no SDK
dependency). generationConfig.responseMimeType requests JSON output; callers
must still validate (app/services/json_repair.py) — Gemini can still wrap or
malform JSON despite the MIME type.
"""
import httpx

from app.ai.base import AIProvider
from app.core.config import get_settings

settings = get_settings()


class GeminiProvider(AIProvider):
    name = "gemini"

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.AI_API_KEY:
            raise RuntimeError("AI_API_KEY is required for AI_PROVIDER=gemini")
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL}:generateContent",
            params={"key": settings.AI_API_KEY},
            json={
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
            },
            timeout=120,
        )
        response.raise_for_status()
        parts = response.json()["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts)