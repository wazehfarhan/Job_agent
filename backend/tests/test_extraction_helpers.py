"""Unit tests for the Extraction Agent's defensive coercion helpers — the
"never invent data" layer: anything the model can't confidently provide
falls back to null/unspecified, never to a guessed value."""
from app.agents.extraction import (
    _as_enum,
    _as_float,
    _as_list,
    _as_str,
    _strip_html,
)
from app.models.job import WorkMode


def test_as_str():
    assert _as_str("  x ") == "x"
    assert _as_str("") is None
    assert _as_str("   ") is None
    assert _as_str(None) is None
    assert _as_str(42) == "42"


def test_as_float():
    assert _as_float("12.5") == 12.5
    assert _as_float(12) == 12.0
    assert _as_float("") is None
    assert _as_float(None) is None
    assert _as_float("abc") is None  # unparsable → None, never 0 or a guess


def test_as_list():
    assert _as_list([" a ", "b", ""]) == ["a", "b"]
    assert _as_list([]) == []
    assert _as_list(None) == []
    assert _as_list("not-a-list") == []


def test_as_enum():
    assert _as_enum("REMOTE", WorkMode, WorkMode.unspecified) is WorkMode.remote
    assert _as_enum(" Hybrid ", WorkMode, WorkMode.unspecified) is WorkMode.hybrid
    assert _as_enum("bogus", WorkMode, WorkMode.unspecified) is WorkMode.unspecified
    assert _as_enum(None, WorkMode, WorkMode.unspecified) is WorkMode.unspecified


def test_strip_html():
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert _strip_html(None) is None
    assert _strip_html("") is None
    assert _strip_html("   ") is None