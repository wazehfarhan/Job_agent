"""Tests for app/sources/registry.py — JOB_SOURCE_CONFIG enablement (T1.8)."""
import pytest

from app.core.config import get_settings
import app.sources.remotive  # noqa: F401 — importing registers the remotive adapter
from app.sources.registry import _REGISTRY, get_enabled_sources, get_source


@pytest.fixture(autouse=True)
def _fresh_settings_cache():
    # get_settings() is lru_cached; clear before/after so JOB_SOURCE_CONFIG
    # overrides via monkeypatch.setenv actually take effect.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_every_registered_source_known():
    assert "remotive" in _REGISTRY


def test_empty_config_enables_all(monkeypatch):
    monkeypatch.setenv("JOB_SOURCE_CONFIG", "{}")
    names = [type(source).name for source in get_enabled_sources()]
    assert "remotive" in names


def test_explicit_true_enables_only_that_source(monkeypatch):
    monkeypatch.setenv("JOB_SOURCE_CONFIG", '{"remotive": true}')
    names = [type(source).name for source in get_enabled_sources()]
    assert names == ["remotive"]


def test_explicit_false_disables(monkeypatch):
    monkeypatch.setenv("JOB_SOURCE_CONFIG", '{"remotive": false}')
    assert get_enabled_sources() == []


def test_unknown_source_in_config_is_ignored(monkeypatch):
    monkeypatch.setenv("JOB_SOURCE_CONFIG", '{"greenhouse": true}')
    assert get_enabled_sources() == []


def test_invalid_json_falls_back_to_all_enabled(monkeypatch):
    monkeypatch.setenv("JOB_SOURCE_CONFIG", "not-json-at-all")
    names = [type(source).name for source in get_enabled_sources()]
    assert "remotive" in names


def test_get_source_bypasses_enablement(monkeypatch):
    # Extraction needs the adapter that discovered the job even if that
    # source's discovery is now toggled off.
    monkeypatch.setenv("JOB_SOURCE_CONFIG", '{"remotive": false}')
    assert get_source("remotive") is not None
    assert get_source("does-not-exist") is None