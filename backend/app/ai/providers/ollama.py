"""
Ollama provider — fully local, free, no API key, nothing leaves the machine
(sections 3 and 42). Default provider per AI_PROVIDER (section 44: only
adapters that are actually implemented are wired in — see factory.py).

Uses Ollama's /api/chat endpoint with format="json" for JSON-mode output.
Even with format="json" set, Ollama's own docs note models can still leak
preamble or invent fields — callers must validate (see json_repair.py).
"""
import httpx

from app.ai.base import AIProvider
from app.core.config import get_settings

settings = get_settings()


class OllamaProvider(AIProvider):
    name = "ollama"

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": "json",
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def embed(self, text: str) -> list[float]:
        """Embeddings via Ollama's /api/embeddings endpoint (AI_EMBED_MODEL)."""
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": settings.AI_EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["embedding"]