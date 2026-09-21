"""Tests for app/core/security.py — password hashing + JWT round-trip."""
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_jwt_roundtrip():
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_jwt_garbage_token_is_none():
    assert decode_access_token("not-a-token") is None
    assert decode_access_token("") is None