"""
JSON repair for LLM output (section 23, Todo T1.2) — models routinely wrap
JSON in markdown fences or add preamble, and sometimes emit trailing commas.
parse_json() finds the first balanced JSON object in the text (string-aware
brace matching), tries it as-is, applies last-resort fixes, and raises
ValueError with a clear message when nothing salvageable is present. Callers
decide how to surface failures — nothing here invents data (section 44).
"""
import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_LEADING_FENCE = re.compile(r"^```[a-zA-Z]*\s*")
_TRAILING_FENCE = re.compile(r"\s*```$")


def _first_json_object(text: str) -> str | None:
    """Return the first balanced {...} span, ignoring braces inside strings."""
    in_string = False
    escaped = False
    depth = 0
    start: int | None = None
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start : index + 1]
    return None


def parse_json(text: str) -> dict[str, Any]:
    """Extract and parse the first JSON object found in `text`."""
    cleaned = _TRAILING_FENCE.sub("", _LEADING_FENCE.sub("", (text or "").strip())).strip()
    span = _first_json_object(cleaned)
    if span is None:
        raise ValueError("no JSON object found in model output")
    try:
        data = json.loads(span)
    except json.JSONDecodeError:
        # Last-resort fix: trailing commas before } or ] (JSONDecodeError is a
        # ValueError, so a still-broken object surfaces to the caller as one).
        fixed = re.sub(r",\s*([}\]])", r"\1", span)
        data = json.loads(fixed)
    if not isinstance(data, dict):
        raise ValueError("model output JSON is not an object")
    return data


def parse_model(text: str, schema: type[T]) -> T:
    """parse_json + pydantic validation, for callers that want typed output."""
    return schema.model_validate(parse_json(text))