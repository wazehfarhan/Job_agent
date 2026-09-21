"""
JobSource — the interface every job-board adapter must implement (section 8).

Adding a new source means writing one adapter class here and registering it
in `registry.py`; nothing else in the codebase should know which sources
exist. Adapters must only use permitted methods (public APIs, official feeds,
or scraping that a site's terms of service allow) — see section 25/26.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class JobSearchCriteria:
    keywords: list[str]
    location: str | None = None
    remote_only: bool = False
    employment_type: str | None = None  # internship | full_time | part_time | contract


@dataclass
class DiscoveredJob:
    """Metadata returned by search — `description` carries whatever raw
    content the source returned in the same response (adapters with per-job
    detail endpoints may leave it None and serve get_job_details instead)."""
    source: str
    source_job_id: str | None
    url: str
    title: str | None = None
    company: str | None = None
    description: str | None = None


class JobSource(ABC):
    """Base class for a single job-board/API adapter."""

    name: str  # unique identifier, e.g. "greenhouse", "linkedin_api"

    @abstractmethod
    def search_jobs(self, criteria: JobSearchCriteria) -> list[DiscoveredJob]:
        """Return newly discovered job listings matching the given criteria."""
        raise NotImplementedError

    @abstractmethod
    def get_job_details(self, url: str) -> str:
        """Return the raw job page content/description for extraction."""
        raise NotImplementedError
