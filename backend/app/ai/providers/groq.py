"""
Groq provider — free tier via the OpenAI-compatible chat completions API,
called with httpx (no SDK dependency). response_format json_object requests
JSON output; callers must still validate (app/services/json_repair.py).
"""
import httpx

from app.ai.base import AIProvider
from app.core.config import get_settings

settings = get_settings()

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(AIProvider):
    name = "groq"

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.AI_API_KEY:
            raise RuntimeError("AI_API_KEY is required for AI_PROVIDER=groq")
        response = httpx.post(
            _GROQ_API_URL,
            headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
            json={
                "model": settings.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]