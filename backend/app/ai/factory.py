"""
AI provider factory — resolves AI_PROVIDER (section 5: no vendor lock-in) to
a concrete adapter. Only adapters that actually exist in app/ai/providers/
are wired in (per the "never fake it" rule); unknown or unimplemented choices
fail loudly instead of pretending. Adding a provider = write the adapter
class + one branch here (Implementation.md §13).

complete_json() returns RAW text — parsing, validation, and repair stay the
caller's responsibility (app/services/json_repair.py). embed() is an optional
capability (see base.py); only Ollama implements it today.
"""
from app.ai.base import AIProvider
from app.core.config import get_settings

_KEYED_PROVIDERS = {"gemini", "groq", "anthropic", "openai"}


def get_provider() -> AIProvider:
    """Return the AIProvider selected by AI_PROVIDER (settings are cached)."""
    settings = get_settings()

    if settings.AI_PROVIDER in _KEYED_PROVIDERS and not settings.AI_API_KEY:
        # Fail fast with a message the user can act on.
        raise RuntimeError(
            f"AI_PROVIDER={settings.AI_PROVIDER!r} requires AI_API_KEY in .env"
        )

    if settings.AI_PROVIDER == "ollama":
        from app.ai.providers.ollama import OllamaProvider

        return OllamaProvider()
    if settings.AI_PROVIDER == "gemini":
        from app.ai.providers.gemini import GeminiProvider

        return GeminiProvider()
    if settings.AI_PROVIDER == "groq":
        from app.ai.providers.groq import GroqProvider

        return GroqProvider()
    if settings.AI_PROVIDER == "anthropic":
        from app.ai.providers.anthropic import AnthropicProvider

        return AnthropicProvider()

    raise NotImplementedError(
        f"AI_PROVIDER={settings.AI_PROVIDER!r} has no implemented adapter yet. "
        "Implemented: ['ollama', 'gemini', 'groq', 'anthropic']. Add one under "
        "app/ai/providers/ and wire a branch here (see Implementation.md §13)."
    )