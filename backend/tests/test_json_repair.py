"""Tests for app/services/json_repair.py — the LLM-output repair layer."""
import pytest
from pydantic import BaseModel

from app.services.json_repair import parse_json, parse_model


def test_parses_clean_object():
    assert parse_json('{"a": 1}') == {"a": 1}


def test_strips_markdown_fences():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('```\n{"a": 1}\n```') == {"a": 1}


def test_strips_preamble_and_trailing_text():
    assert parse_json('Here is your JSON:\n{"a": 1}\nHope that helps!') == {"a": 1}


def test_braces_inside_strings_are_ignored():
    assert parse_json('{"s": "curly { braces } inside", "a": 1}') == {
        "s": "curly { braces } inside",
        "a": 1,
    }


def test_fixes_trailing_commas():
    assert parse_json('{"a": 1, "b": [1, 2,],}') == {"a": 1, "b": [1, 2]}


def test_extracts_first_object_from_surroundings():
    assert parse_json('x {"outer": {"inner": 2}} y') == {"outer": {"inner": 2}}


def test_no_json_raises_value_error():
    with pytest.raises(ValueError):
        parse_json("there is no json here at all")


def test_non_object_json_raises():
    with pytest.raises(ValueError):
        parse_json("[1, 2, 3]")


def test_none_and_empty_raise():
    with pytest.raises(ValueError):
        parse_json("")
    with pytest.raises(ValueError):
        parse_json(None)  # type: ignore[arg-type]


class _Schema(BaseModel):
    name: str
    score: int


def test_parse_model_validates():
    parsed = parse_model('{"name": "backend", "score": 88}', _Schema)
    assert parsed.name == "backend"
    assert parsed.score == 88


def test_parse_model_rejects_mismatched_payload():
    # pydantic's ValidationError subclasses ValueError, so callers can catch
    # parse failures and validation failures with one except clause.
    with pytest.raises(ValueError):
        parse_model('{"name": 123}', _Schema)