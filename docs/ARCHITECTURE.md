# Architecture

## Pipeline

```
Job Discovery Agent → Job Extraction Agent → Deduplication → Matching Agent
    → Application Preparation Agent → Human Approval → Browser/Application Agent
    → Application Tracking Agent
```

Each stage is a separate, testable component — not one monolithic agent.
Matching combines rule-based eligibility checks, structured skill comparison,
semantic similarity (pgvector embeddings), and LLM reasoning; it never relies
on the LLM alone.

**Status:** Discovery (`app/services/discovery.py` + `app/sources/`),
Extraction (`app/agents/extraction.py`), and Matching (`app/agents/matching.py`)
are implemented. Preparation, approval, browser automation, and tracking UI
are next.

## Data model (core tables)

- `jobs` — one row per discovered posting (`app/models/job.py`; incl. pgvector `embedding`)
- `applications` — one row per application attempt, keyed to a job + user
- `status_events` — append-only timeline, one row per status transition
- `users`, `profiles`, `resumes`, `skills`, `experiences`, `projects`,
  `certifications`, `preferences` — identity/profile side
- Schema lives in `alembic/versions/0001_initial_schema.py`

## AI provider abstraction

`app/ai/` defines the `Provider` interface (`complete_json`, optional
`embed`) with `AI_PROVIDER` selecting the concrete adapter via
`app/ai/factory.py` — implemented: ollama (default), gemini, groq, anthropic.
The app is never locked to one vendor.

## Job sources

`app/sources/base.py` defines the `JobSource` interface (`search_jobs`,
`get_job_details`). Sources are adapters registered in
`app/sources/registry.py` and toggled via `JOB_SOURCE_CONFIG`. Implemented:
`remotive` (official free API, rate-limit aware, attribution preserved).

## Development order

Following the spec's phased plan: project structure → Postgres/Redis →
FastAPI backend (done) → auth → profile → CV upload/parsing → job DB (done)
→ source abstraction (done) → first real source (done) → extraction (done)
→ matching (done) → dashboard → application prep → review → Playwright
automation → real workflows → notifications → tracking → scheduler → tests
→ Docker → security review → E2E testing.