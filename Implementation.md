# Implementation Guide — how the system is built today

Companion to [Feature.md](Feature.md) (what exists) and [Todo.md](Todo.md) (what's next).
Everything below reflects the current code, not aspirations. Reviewed 2026-09-21.

## 1. Runtime topology

```
Browser (planned) ──┐
                    ├─► FastAPI (uvicorn, :8000) ──► PostgreSQL 16 + pgvector (:5432)
Celery worker ──────┤                   │
Celery beat ────────┴──► Redis 7 (:6379) ◄┘  (broker / result backend / cache client)
```

- Entry point: `backend/app/main.py` — creates the FastAPI app, mounts CORS
  from `ALLOWED_ORIGINS` (comma-separated env), includes routers under
  `settings.API_PREFIX` (`/api`): auth, jobs, profile, resumes, applications.
  Exposes `GET /api/health`.
- Python **3.12** (see `backend/Dockerfile`); the host's system Python 3.9 is not
  sufficient — the code uses `X | None` annotations and SQLAlchemy 2.0 typed mappings.

## 2. Layering

```
api/        HTTP routers (thin) — validate via schemas/, call services/agents/models
schemas/    Pydantic request/response — auth, profile, resume, job, application
services/   domain logic — discovery (dedup + content_hash), resume_parser, json_repair
agents/     pipeline agents — extraction.py, matching.py (prompts in ../prompts/)
models/     SQLAlchemy ORM — 12 tables (§3)
core/       config (pydantic-settings), database (engine/session/Base),
            security (bcrypt + JWT), deps (get_current_user), redis (client)
sources/    JobSource adapters + registry (JOB_SOURCE_CONFIG-aware)
ai/         AIProvider abstraction, factory (4 adapters), ollama/gemini/groq/anthropic
browser/    (empty) Playwright automation lands here
tasks/      Celery app (app/tasks/celery_app.py); real tasks land here
```

Request flow: `HTTP → router → get_current_user (JWT) → get_db (session) → service/agent → Pydantic response`.

## 3. Data model

Every table inherits `TimestampedBase` (`app/models/base.py`): `id UUID (uuid4)`,
`created_at`, `updated_at` (server default now / onupdate now).
Schema: `alembic/versions/0001_initial_schema.py` (12 tables, 5 enum types,
pgvector extension + hnsw cosine index on `jobs.embedding`).

```
users ─1:1─ profiles ─1:N─ educations      (institution, degree, field, GPA optional)
                    ├─1:N─ certifications  (name, issuer, date, credential_url)
                    ├─1:N─ skills          (category enum: 10 categories)
                    ├─1:N─ experiences     (org, role, dates, skills_used[], achievements[])
                    ├─1:N─ projects        (technologies[], links, achievements[])
                    └─1:1─ preferences     (roles, types, locations, work modes,
                                            min_salary/min_stipend, keywords,
                                            excluded_companies/roles, min_match_score)

users ─1:N─ resumes   (label, original_filename, file_path, file_type pdf|docx,
                       parsed_text, structured_data JSON — reserved, is_default)

jobs                  (source, source_job_id, url, company, title, description,
                       location, work_mode, employment_type, salary_min/max,
                       currency, required_skills[], preferred_skills[],
                       experience/education_requirement, deadline,
                       application_url, posted_at, discovered_at,
                       status, content_hash, embedding vector(768))

users ─1:N─ applications ─N:1─ jobs
      applications ─1:N─ status_events  (append-only timeline)
      application: resume_id FK, cover_letter, answers_json,
                   match_score int, match_category, match_reasons text[]
```

**Enums**

- `WorkMode` remote / hybrid / onsite / unspecified · `EmploymentType` internship / full_time / part_time / contract / unspecified
- `JobStatus` discovered → extracted → {duplicate, matched, ineligible, expired}
- `ApplicationStatus` discovered → analyzing → matched → preparing → awaiting_approval → approved → submitting → applied → {interview, rejected, withdrawn, failed, needs_user_action}
- `SkillCategory` programming_language, framework, library, database, cloud, ai_ml, nlp, devops, testing, other

## 4. Auth implementation

- `POST /api/auth/register` → email uniqueness check (409 on duplicate), bcrypt
  hash via passlib `CryptContext(schemes=["bcrypt"])`, returns `UserOut` (201).
- `POST /api/auth/login` → `OAuth2PasswordRequestForm` (the `username` field
  carries the email), 401 on failure with `WWW-Authenticate: Bearer`, returns
  `{access_token, token_type: "bearer"}`. Token: python-jose, HS256,
  `sub = user_id`, `exp = now + ACCESS_TOKEN_EXPIRE_MINUTES` (24 h).
- `get_current_user` (`core/deps.py`): `OAuth2PasswordBearer(tokenUrl="/api/auth/login")`
  → decode token → load user → 401 unless found and `is_active`.

## 5. Job discovery & deduplication

- `sources/base.py` — `JobSource` ABC: `search_jobs(criteria) -> list[DiscoveredJob]`,
  `get_job_details(url) -> str` (raw content for extraction). `DiscoveredJob`
  carries `source`, `source_job_id`, `url`, `title`, `company`, `description`.
- `sources/registry.py` — `@register` decorator fills `_REGISTRY[name] → class`;
  `get_enabled_sources()` consults `JOB_SOURCE_CONFIG` (JSON map name → bool;
  `{}` = all registered); `get_source(name)` bypasses enablement for extraction.
- `sources/remotive.py` — `@register`ed adapter for `https://remotive.com/api/remote-jobs`
  (no key). Rate-limit compliance is documented in the module docstring: ≤ ~4
  calls/day, ≤ 2/min → exactly **one** HTTP GET per discovery run, and full
  descriptions are cached from that same response so `get_job_details` normally
  makes zero extra calls. Attribution preserved: `url` stays Remotive's listing
  URL and `source` stays `"remotive"`.
- `services/discovery.py` — per source: try/except around `search_jobs` (a
  broken source is logged and skipped, never corrupting the run — NFR-7);
  per item: `SELECT … WHERE source = … AND source_job_id = …`; insert only new
  rows with `description` + `content_hash`; single commit; returns only new
  rows. Idempotent: running twice discovers nothing new.

## 6. AI layer

- `ai/base.py` — `AIProvider.complete_json(system, user) -> str` returns **raw
  text** deliberately; callers must parse/validate via `services/json_repair.py`.
  `embed(text) -> list[float]` is an optional capability (base raises
  `NotImplementedError`; matching treats that as "similarity unavailable").
- `ai/factory.py` — `get_provider()` resolves `AI_PROVIDER`, fail-fasts on a
  missing `AI_API_KEY` for hosted providers, and raises `NotImplementedError`
  for unimplemented choices. Implemented: **ollama** (default, local, also
  embeddings), **gemini** (REST + responseMimeType JSON), **groq**
  (OpenAI-compatible + json_object), **anthropic** (pinned SDK). openai has no
  adapter yet — the factory says so explicitly.
- `services/json_repair.py` — strips code fences/preamble, extracts the first
  balanced JSON object (string-aware brace matching), fixes trailing commas,
  raises `ValueError` when nothing salvageable exists; `parse_model()` adds
  pydantic validation.

## 7. Pipeline agents

- **Extraction** (`agents/extraction.py`, prompts in `prompts/extraction.py`):
  `extract_job(db, job)` — gets the raw description from the job's source
  adapter (HTML stripped), prompts the provider, parses via `parse_json`,
  coerces every field defensively (`_as_str/_as_float/_as_list/_as_enum` —
  invalid values fall back to null/unspecified, never invented), sets
  `status=extracted`, refreshes `content_hash`, and best-effort embeds the
  description (a missing embedding model never fails extraction).
  `extract_pending_jobs(db, limit)` batch-processes `discovered` jobs,
  logging and skipping failures.
- **Matching** (`agents/matching.py`, prompts in `prompts/matching.py`):
  `match_job(db, job, user)` runs the spec pipeline — `_rule_eligibility`
  (hard filters from preferences → `ineligible`), `_skill_overlap` (required
  vs owned skills), cosine similarity (job embedding vs profile-text
  embedding, optional), `_llm_score` (0–100 + category + reasons, optional,
  never raises). Score/category/reasons persist on the application; a
  `StatusEvent` is appended for `discovered → matched`; the LLM can never
  overrule a hard rule failure.

## 8. Resume pipeline & uploads

`POST /api/resumes` (multipart `label` + `file`): extension whitelist
{pdf, docx} → 400; size ≤ `MAX_UPLOAD_MB` → 413; write to
`UPLOAD_DIR/<user_id>/<uuid4>.<ext>` (UUID name — path-traversal safe);
`services/resume_parser.extract_text` (pypdf `PdfReader` / python-docx
`Document`); on exception the file is still stored with `parsed_text = NULL`
(scanned PDFs surface as null, never guessed). `set-default` clears
`is_default` on the user's other resumes first; `delete` unlinks the file
from disk, then deletes the row (204).

## 9. Docker

`docker-compose.yml` services: `postgres` (pgvector/pgvector:pg16),
`redis` (redis:7-alpine), `backend` (build `./backend`, uvicorn `--reload`,
port 8000), `worker` / `scheduler` (celery worker/beat on
`app/tasks/celery_app.py`), `frontend` (build `./frontend` — unbuildable
until Next.js is scaffolded, T2.1). Volumes: named `pgdata`; live source
binds for backend/worker/scheduler/frontend (anonymous `/app/node_modules`
for the frontend). Use `.env.docker.example` → `.env` so in-network
hostnames resolve. First-boot sequence:

```bash
docker compose up postgres redis
docker compose run --rm backend alembic upgrade head   # creates all 12 tables
docker compose up
```

## 10. Testing

`backend/tests/` contains only `__init__.py`. pytest + pytest-asyncio are
pinned in `requirements.txt`, but nothing is tested yet — T3.4 defines the
suite.

## 11. Open items / technical debt (as of 2026-09-21)

| Item | Tracking |
|------|----------|
| Migration `0001` is hand-written — verify `alembic upgrade head` against a live Postgres | T0.2 note |
| Frontend written but never executed — run `npm install && npm run dev`; commit the lockfile after | T2.1 note |
| Celery beat schedule + real tasks | T3.1 |
| Playwright browser agent | T3.2 |
| Notifications | T3.3 |
| Test suite + CI + LICENSE | T3.4–T3.5 |
| Per-user discovery criteria not wired end-to-end | FR-15 |
| Docs upkeep | T4.4 (ongoing) |

> Resolved 2026-09-21 (P0 + P1): boot blocker (resume schemas), Celery app,
> compose networking, AI factory + 3 new providers, `.env` alignment, jobs
> 404 + response models, extraction agent, json_repair, embeddings +
> pgvector, matching agent, applications API, content_hash,
> JOB_SOURCE_CONFIG, CORS from env, model re-exports.

## 12. How to add a new job source (pattern)

```python
# backend/app/sources/greenhouse.py
import httpx
from app.sources.base import DiscoveredJob, JobSearchCriteria, JobSource
from app.sources.registry import register

@register
class GreenhouseSource(JobSource):
    name = "greenhouse"

    def search_jobs(self, criteria: JobSearchCriteria) -> list[DiscoveredJob]:
        ...  # call the public API; map results to DiscoveredJob(source=self.name, ...)

    def get_job_details(self, url: str) -> str:
        ...  # raw page/description content for the extraction agent
```

Rules: only permitted methods (public APIs / official feeds / ToS-permitted
scraping); preserve attribution and rate limits; register via the decorator;
optionally add `{"greenhouse": true}` to `JOB_SOURCE_CONFIG` — nothing else
in the codebase changes.

## 13. How to add a new AI provider (pattern)

```python
# backend/app/ai/providers/openai.py
from app.ai.base import AIProvider
from app.core.config import get_settings

class OpenAIProvider(AIProvider):
    name = "openai"

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...  # call the API; return RAW text — validation is the caller's job
```

Then add the branch to `get_provider()` in `app/ai/factory.py` (and pin the
SDK in requirements.txt if you use one rather than httpx).