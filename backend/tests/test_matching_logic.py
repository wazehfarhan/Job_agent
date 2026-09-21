"""Unit tests for the Matching Agent's pure helpers (no DB, no LLM)."""
import pytest

from app.agents.matching import _cosine, _rule_eligibility, _skill_overlap
from app.models.job import Job, WorkMode
from app.models.preference import Preferences
from app.models.profile import Profile
from app.models.skill import Skill


def make_job(**overrides) -> Job:
    defaults = dict(source="remotive", url="https://example.com/job")
    defaults.update(overrides)
    return Job(**defaults)


def make_profile(skills=()) -> Profile:
    return Profile(skills=[Skill(name=name) for name in skills])


# --- _cosine -----------------------------------------------------------------


def test_cosine_basics():
    assert _cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert _cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert _cosine([1, 2], [2, 4]) == pytest.approx(1.0)
    assert _cosine([1, 0], [0, -1]) == pytest.approx(-1.0)


def test_cosine_handles_degenerate_input():
    assert _cosine(None, [1]) is None
    assert _cosine([1], None) is None
    assert _cosine([], [1]) is None
    assert _cosine([1, 2], [1]) is None  # length mismatch
    assert _cosine([0, 0], [1, 1]) is None  # zero vector


# --- _skill_overlap ----------------------------------------------------------


def test_skill_overlap_normalizes_and_matches():
    job = make_job(required_skills=["Python", " SQL ", "docker"])
    profile = make_profile(skills=["python", "Docker", "pandas"])
    ratio, matched = _skill_overlap(job, profile)
    assert ratio == pytest.approx(2 / 3)
    assert matched == ["docker", "python"]


def test_skill_overlap_no_requirements_is_neutral():
    ratio, matched = _skill_overlap(make_job(), make_profile(skills=["python"]))
    assert (ratio, matched) == (0.0, [])


# --- _rule_eligibility -------------------------------------------------------


def test_rule_eligibility_no_preferences_is_eligible():
    assert _rule_eligibility(make_job(), None) == []


def test_rule_eligibility_work_mode():
    prefs = Preferences(work_modes=["remote"])
    assert _rule_eligibility(make_job(work_mode=WorkMode.onsite), prefs) != []
    assert _rule_eligibility(make_job(work_mode=WorkMode.remote), prefs) == []


def test_rule_eligibility_salary_floor():
    prefs = Preferences(min_salary=100_000)
    assert _rule_eligibility(make_job(salary_max=80_000), prefs) != []
    # Unknown salary never hard-fails — absence is not disqualification.
    assert _rule_eligibility(make_job(salary_max=None), prefs) == []


def test_rule_eligibility_exclusions():
    prefs = Preferences(excluded_companies=["meta"], excluded_roles=["senior"])
    assert _rule_eligibility(make_job(company="Meta"), prefs) != []
    assert _rule_eligibility(make_job(title="Senior Backend Engineer"), prefs) != []
    assert _rule_eligibility(make_job(company="Acme", title="Backend Engineer"), prefs) == []


def test_rule_eligibility_preferred_locations():
    prefs = Preferences(preferred_locations=["berlin"])
    assert _rule_eligibility(make_job(location="Berlin, Germany"), prefs) == []
    assert _rule_eligibility(make_job(location="Tokyo, Japan"), prefs) != []