"""Tests for app/services/discovery.py — content hashing (section 9 change detection)."""
import hashlib

from app.services.discovery import content_hash


def test_none_and_empty_are_none():
    assert content_hash(None) is None
    assert content_hash("") is None
    assert content_hash("   \n\t  ") is None  # whitespace-only counts as empty


def test_whitespace_and_case_insensitive():
    assert content_hash("Hello  WORLD") == content_hash("hello world")
    assert content_hash("  A\n\tB ") == content_hash("a b")


def test_different_text_different_hash():
    assert content_hash("python developer") != content_hash("data engineer")


def test_hash_is_sha256_hex():
    value = content_hash("abc")
    assert len(value) == 64
    assert value == hashlib.sha256(b"abc").hexdigest()