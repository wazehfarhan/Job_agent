"""
Registry of JobSource adapters + enablement via JOB_SOURCE_CONFIG.

JOB_SOURCE_CONFIG is a JSON object mapping source name → bool, e.g.
'{"remotive": true}'. Empty / `{}` → every registered source is enabled
(preserves zero-config behavior); a non-empty object enables only the sources
explicitly set to true. Adding a source: write the adapter with @register —
nothing else changes (spec section 8/44).
"""
import json
import logging

from app.core.config import get_settings
from app.sources.base import JobSource

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, type[JobSource]] = {}


def register(source_cls: type[JobSource]) -> type[JobSource]:
    _REGISTRY[source_cls.name] = source_cls
    return source_cls


def _config() -> dict:
    raw = get_settings().JOB_SOURCE_CONFIG
    try:
        parsed = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError:
        logger.warning("JOB_SOURCE_CONFIG is not valid JSON (%r); enabling all registered sources", raw)
        return {}
    return parsed if isinstance(parsed, dict) else {}


def get_enabled_sources() -> list[JobSource]:
    """Instantiate every registered, enabled source (see module docstring)."""
    config = _config()
    if not config:
        return [cls() for cls in _REGISTRY.values()]
    return [cls() for name, cls in _REGISTRY.items() if config.get(name) is True]


def get_source(name: str) -> JobSource | None:
    """Look up one adapter by name (used by the Extraction Agent). Deliberately
    ignores enablement — extraction needs the adapter that discovered the job
    even if discovery for that source is now toggled off."""
    cls = _REGISTRY.get(name)
    return cls() if cls is not None else None