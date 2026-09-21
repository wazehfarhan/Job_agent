"""
Remotive job source adapter — official free public API, no key required.

Per Remotive's terms (https://github.com/remotive-com/remote-jobs-api):
- Must link back to each job's Remotive URL and credit Remotive as the
  source. Both are preserved as-is: DiscoveredJob.url is Remotive's own
  listing URL, and Job.source is always "remotive" — never stripped or
  rehosted.
- Don't call more than ~4x/day, never more than 2x/minute. This adapter
  makes exactly one request per discover_jobs() run (see
  app/services/discovery.py) and caches full descriptions from that same
  response, so get_job_details() never triggers a second call in the
  normal flow. The scheduler (section 27) should run discovery about once
  a day, not on every page load.
"""
import httpx

from app.sources.base import DiscoveredJob, JobSearchCriteria, JobSource
from app.sources.registry import register

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"


@register
class RemotiveSource(JobSource):
    name = "remotive"

    def __init__(self):
        self._description_cache: dict[str, str] = {}

    def search_jobs(self, criteria: JobSearchCriteria) -> list[DiscoveredJob]:
        params = {}
        if criteria.keywords:
            params["search"] = " ".join(criteria.keywords)

        response = httpx.get(REMOTIVE_API_URL, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()

        jobs: list[DiscoveredJob] = []
        for raw in payload.get("jobs", []):
            job_type = raw.get("job_type")
            if criteria.employment_type and job_type and job_type != criteria.employment_type:
                continue

            url = raw.get("url")
            description = raw.get("description", "") or ""
            self._description_cache[url] = description
            jobs.append(
                DiscoveredJob(
                    source=self.name,
                    source_job_id=str(raw.get("id")),
                    url=url,
                    title=raw.get("title"),
                    company=raw.get("company_name"),
                    description=description,
                )
            )
        return jobs

    def get_job_details(self, url: str) -> str:
        if url in self._description_cache:
            return self._description_cache[url]
        # Not cached (e.g. called without a prior search_jobs on this
        # instance). Remotive has no single-job endpoint, so refetch the
        # full list once and try again — still just one extra request.
        self.search_jobs(JobSearchCriteria(keywords=[]))
        return self._description_cache.get(url, "")