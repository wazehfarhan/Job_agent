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
  (hardcoded `http://localhost:3000`), includes routers under `settings.API_PREFIX`
  (`/api`), exposes `GET /api/health`.
- Python **3.12** (see `backend/Dockerfile`); the host's system Python 3.9 is not
  sufficient — the code uses `X | None` annotations and SQLAlchemy 2.0 typed mappings.

## 2. Layering

```
api/        HTTP routers (thin) — validate via schemas/, call services/models
schemas/    Pydantic request/response — auth, profile (resume module misplaced → T0.1)
services/   domain logic — discovery (dedup), resume_parser (pypdf / python-docx)
models/     SQLAlchemy ORM — 12 tables (§3)
core/       config (pydantic-settings), database (engine/session/Base),
            security (bcrypt + JWT), deps (get_current_user), redis (client)
sources/    JobSource adapters + registry
ai/         AIProvider abstraction (base, factory, ollama adapter)
agents/ prompts/ browser/ → empty placeholders for pipeline stages
tasks/      → Celery app (`app/tasks/celery_app.py`); real tasks land here
```

Request flow: `HTTP → router → get_current_user (JWT) → get_db (session) → service/model → Pydantic response`.

## 3. Data model

Every table inherits `TimestampedBase` (`app/models/base.py`): `id UUID (uuid4)`,
`created_at`, `updated_at` (server default now / onupdate now).

```
users ─1:1─ profiles ─1:N─ educations      (institution, degree, field, GPA optional)
                    ├─1:N─ certifications  (name, issuer, date, credential_url)
                    ├─1:N─ skills          (category enum: 10 categories)
                    ├─1:N─ experiences     (org, role, dates, description,
                    │                       skills_used[], achievements[])
                    ├─1:N─ projects        (name, description, technologies[],
                    │                       url, github_url, responsibilities[],
                    │                       achievements[])
                    └─1:1─ preferences     (target_roles, job_types, internship_types,
                                            preferred_locations, work_modes, min_salary,
                                            min_stipend, preferred_industries, keywords,
                                            excluded_companies, excluded_roles,
                                            min_match_score)

users ─1:N─ resumes   (label, original_filename, file_path, file_type pdf|docx,
                       parsed_text, structured_data JSON — reserved, is_default)

jobs                  (source, source_job_id, url, company, title, description,
                       location, work_mode, employment_type, salary_min/max,
                       currency, required_skills[], preferred_skills[],
                       experience_requirement, education_requirement, deadline,
                       application_url, posted_at, discovered_at,
                       status, content_hash)

users ─1:N─ applications ─N:1─ jobs
      applications ─1:N─ status_events  (append-only timeline)
      application: resume_id FK, cover_letter, answers_json,
                   match_score int, match_category strong|possible|weak|ineligible
```

**Enums**

- `WorkMode` remote / hybrid / onsite / unspecified · `EmploymentType` internship / full_time / part_time / contract / unspecified
- `JobStatus` discovered → extracted → {duplicate, matched, ineligible, expired}
- `ApplicationStatus` discovered → analyzing → matched → preparing → awaiting_approval → approved → submitting → applied → {interview, rejected, withdrawn, failed, needs_user_action}
- `SkillCategory` programming_language, framework, library, database, cloud, ai_ml, nlp, devops, testing, other

**Migrations:** `alembic/env.py` imports every model module into `Base.metadata`
and injects `DATABASE_URL` into the Alembic config; `alembic/versions/` is still
empty — generating the initial migration is **T0.2**.

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

- `sources/base.py` — `JobSource` ABC: `search_jobs(criteria) -> list[DiscoveredJob]`
  (minimal metadata), `get_job_details(url) -> str` (raw content for extraction).
  `JobSearchCriteria` carries keywords / location / remote_only / employment_type.
- `sources/registry.py` — `@register` decorator fills `_REGISTRY[name] → class`;
  `get_enabled_sources()` instantiates every registered class. Note: the
  `JOB_SOURCE_CONFIG` toggle exists in settings but is consulted nowhere yet (T1.8).
- `sources/remotive.py` — `@register`ed adapter for `https://remotive.com/api/remote-jobs`
  (no key). Rate-limit compliance is documented in the module docstring: ≤ ~4
  calls/day, ≤ 2/min → exactly **one** HTTP GET per discovery run, and full
  descriptions are cached from that same response so `get_job_details` normally
  makes zero extra calls. Attribution preserved: `url` stays Remotive's listing
  URL and `source` stays `"remotive"`.
- `services/discovery.py` — for each enabled source → for each item →
  `SELECT … WHERE source = … AND source_job_id = …`; insert only new rows; a
  single commit at the end; returns only the newly created rows. Idempotent:
  running twice discovers nothing new.

## 6. AI layer

- `ai/base.py` — `AIProvider.complete_json(system_prompt, user_prompt) -> str`
  returns **raw text** deliberately; callers must parse/validate it (the JSON
  repair service is planned but not yet created — T1.2).
- `ai/providers/ollama.py` — POSTs to `{OLLAMA_BASE_URL}/api/chat` with
  `format: "json"`, `stream: false`, model from `AI_MODEL`, timeout 120 s →
  returns `message.content`.
- `ai/factory.py` — `get_provider()` resolves `AI_PROVIDER` to a concrete
  adapter and raises `NotImplementedError` for adapters that don't exist yet.
  Only the Ollama adapter is implemented today; gemini/groq/openai would go
  through `httpx`; the `anthropic` SDK is already pinned in requirements.

## 7. Resume pipeline

`POST /api/resumes` (multipart `label` + `file`):

1. Extension whitelist {pdf, docx} → else 400.
2. Size ≤ `MAX_UPLOAD_MB` → else 413.
3. Write to `UPLOAD_DIR/<user_id>/<uuid4>.<ext>` (UUID name — path-traversal safe).
4. `services/resume_parser.extract_text` (pypdf `PdfReader` / python-docx
   `Document`); on exception the file is still stored with `parsed_text = NULL`
   (never guess content — scanned PDFs surface as null).
5. Insert `resumes` row → 201 with `ResumeDetailOut`.

Also: `set-default` clears `is_default` on all of the user's other resumes
first; `delete` unlinks the file from disk, then deletes the row (204).

## 8. Configuration reference

Defined once in `core/config.py` (pydantic-settings, `.env`, cached via
`@lru_cache`); full table in [README.md](README.md). Required at boot (no
defaults → fail fast): `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`.

## 9. Docker

`docker-compose.yml` services: `postgres` (pgvector/pgvector:pg16),
`redis` (redis:7-alpine), `backend` (build `./backend`, uvicorn `--reload`,
port 8000), `worker` / `scheduler` (celery worker/beat on the now-implemented
`app/tasks/celery_app.py`), `frontend` (build `./frontend`
— unbuildable until Next.js is scaffolded, T2.1). Volumes: named `pgdata`;
live source binds for backend/worker/scheduler/frontend (with an anonymous
`/app/node_modules` volume for the frontend).

## 10. Testing

`backend/tests/` contains only `__init__.py`. pytest + pytest-asyncio are
pinned in `requirements.txt`, but nothing is tested yet — see T3.4 for the
planned suite.

## 11. Known issues / technical debt (as of 2026-09-21)

| Issue | Impact | Tracking |
|-------|--------|----------|
| No Alembic migration generated | No tables → every DB endpoint 500s at runtime | T0.2 (needs a live Postgres to autogenerate against) |
| `JOB_SOURCE_CONFIG` parsed nowhere | Source toggles not honored | T1.8 |
| No vector columns despite pgvector dependency | Matching/similarity blocked | T1.3 |
| `json_repair.py` referenced in docstrings but not created | Extraction blocked | T1.2 |
| CORS hardcoded to `http://localhost:3000` | Deploy friction | T4.3 |
| No LICENSE, CI, or tests yet | Safety / reproducibility | T3.4–T3.5 |
| `frontend/` has no package.json | compose `frontend` image unbuildable | T2.1 |

> Resolved 2026-09-21: resume schemas moved to `app/schemas/resume.py` (boot
> blocker T0.1); `app/tasks/celery_app.py` created (T0.3); `.env.docker.example`
> added with compose-correct hostnames (T0.4); `ai/factory.get_provider()`
> implemented (T0.5); `.env.example` aligned with code defaults (T0.6); jobs
> endpoints now use response models + real 404 (T0.7).

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
nothing else in the codebase changes.

## 13. How to add a new AI provider (pattern)

```python
# backend/app/ai/providers/gemini.py
from app.ai.base import AIProvider
from app.core.config import get_settings

class GeminiProvider(AIProvider):
    name = "gemini"

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...  # call the API; return RAW text — validation is the caller's job
```

Then add the branch to `get_provider()` once `ai/factory.py` is implemented (T0.5).
