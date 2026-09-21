"""
Anthropic provider — uses the pinned anthropic SDK. Anthropic has no JSON
mode, so the system prompt demands raw JSON and callers must validate
(app/services/json_repair.py). Requires a paid API key; not the default
(section 3: free/local tooling first).
"""
from app.ai.base import AIProvider
from app.core.config import get_settings

settings = get_settings()


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.AI_API_KEY:
            raise RuntimeError("AI_API_KEY is required for AI_PROVIDER=anthropic")
        import anthropic  # lazy: only paid-tier runs pay the import cost

        client = anthropic.Anthropic(api_key=settings.AI_API_KEY)
        message = client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=1024,
            system=system_prompt + "\nRespond with ONLY a JSON object.",
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(getattr(block, "text", "") for block in message.content)