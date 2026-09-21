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

## Data model (core tables)

- `jobs` — one row per discovered posting (`app/models/job.py`)
- `applications` — one row per application attempt, keyed to a job + user
- `status_events` — append-only timeline, one row per status transition
- Planned next: `users`, `profiles`, `resumes`, `skills`, `experiences`,
  `projects`, `certifications`, `notifications`

## AI provider abstraction

`app/ai/` will define a `Provider` interface (structured JSON output, tool
calling, embeddings, streaming) with `AI_PROVIDER` selecting the concrete
adapter, so the app is never locked to one vendor.

## Job sources

`app/sources/base.py` defines the `JobSource` interface (`search_jobs`,
`get_job_details`). New sources are adapters registered in
`app/sources/registry.py` and toggled via `JOB_SOURCE_CONFIG` — no source is
wired in yet, per the "never fake discovery" rule.

## Development order

Following the spec's phased plan: project structure → Postgres/Redis →
FastAPI backend (done) → auth → profile → CV upload/parsing → job DB (done)
→ source abstraction (done) → first real source → extraction → matching →
dashboard → application prep → review → Playwright automation → real
workflows → notifications → tracking → scheduler → tests → Docker → security
review → E2E testing.
