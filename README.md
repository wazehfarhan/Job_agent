# AI Job & Internship Application Agent

A self-hosted, personal AI agent that discovers job and internship postings from
permitted sources, matches them against your profile and CV, explains the match,
prepares application materials, and tracks every application's status — always
pausing for your explicit approval before anything is ever submitted.

> **Status: v0.2–v0.6 code shipped.** The full backend pipeline (discovery →
> extraction → matching → applications API) runs, the Celery beat schedule
> automates the sweeps, and the Next.js dashboard is written end-to-end.
> Before first use: `docker compose up postgres redis && docker compose run --rm
> backend alembic upgrade head` (verify the hand-written migration) and
> `cd frontend && npm install` (no lockfile committed yet). See
> [FutureUpdate.md](FutureUpdate.md) · [Todo.md](Todo.md).

## How it works (target pipeline)

```
Job Discovery Agent → Job Extraction Agent → Deduplication → Matching Agent
    → Application Preparation Agent → Human Approval → Browser/Application Agent
    → Application Tracking Agent
```

Each stage is an independently testable component — not one monolithic agent.
Matching combines rule-based eligibility checks, structured skill comparison,
semantic similarity (pgvector embeddings), and LLM reasoning; it never relies
on the LLM alone.

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router) / React / TypeScript / Tailwind |
| API | FastAPI + Pydantic v2 (Python 3.12) |
| Database | PostgreSQL 16 + pgvector |
| Queue | Redis 7 + Celery (worker + beat) |
| Parsing | pypdf (PDF), python-docx (DOCX) |
| Automation | Playwright *(planned — permitted automation only)* |
| AI | Provider-agnostic: local Ollama by default; gemini/groq free-tier adapters; anthropic adapter (paid) — all behind `app/ai/factory.py` |

## Repository layout

```
job-agent/
├── backend/
│   ├── app/
│   │   ├── api/          # routers: auth, jobs, profile, resumes, applications, settings
│   │   ├── core/         # config, database, security, deps, redis
│   │   ├── models/       # SQLAlchemy ORM models (12 tables)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # discovery (dedup), resume parsing, json_repair
│   │   ├── sources/      # JobSource adapters: base, registry, remotive
│   │   ├── ai/           # AIProvider abstraction, factory, 4 provider adapters
│   │   ├── agents/       # extraction + matching pipeline agents
│   │   ├── prompts/      # LLM prompt templates (extraction, matching)
│   │   ├── browser/      # (empty) Playwright automation lands here
│   │   └── tasks/        # Celery app + beat-scheduled pipeline tasks
│   ├── alembic/          # migration setup + 0001_initial_schema
│   ├── tests/            # pure-unit suite (pytest)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Next.js 14 dashboard (needs `npm install` once)
│   ├── app/              # dashboard, login, jobs, applications, resumes, profile, settings
│   ├── components/       # Navbar
│   ├── lib/              # typed API client, auth, hooks
│   └── types/            # API type mirrors of the backend schemas
├── infrastructure/       # (empty — deployment/, docker/)
├── docs/ARCHITECTURE.md  # pipeline + data model notes
├── docker-compose.yml    # postgres, redis, backend, worker, scheduler, frontend
├── .env.example          # local-run defaults (ollama, localhost services)
├── .env.docker.example   # compose-run variant (postgres/redis service hostnames)
├── PRD.md · Feature.md · Todo.md · Implementation.md · FutureUpdate.md
```

## Quick start (Docker)

```bash
cp .env.docker.example .env   # compose hostnames; then set SECRET_KEY
docker compose up postgres redis
docker compose run --rm backend alembic upgrade head   # create all 12 tables
cd frontend && npm install && cd ..                    # first run only
docker compose up                                      # backend :8000 · frontend :3000
```

For AI features, either run Ollama locally (`ollama pull llama3.1
nomic-embed-text`) or set `AI_PROVIDER=gemini|groq` + `AI_API_KEY` (free tiers).

## Running locally (no Docker for the apps)

Requires **Python 3.12** and Node 20:

```bash
docker compose up postgres redis               # infra only
cp .env.example .env                           # fill in SECRET_KEY
cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                           # creates all 12 tables
uvicorn app.main:app --reload                  # terminal 1 → http://localhost:8000
cd ../frontend && npm install && npm run dev   # terminal 2 → http://localhost:3000
```

## API surface (implemented today)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness probe |
| POST | `/api/auth/register` | Create account (email + password ≥ 8 chars, bcrypt) — 201, 409 on duplicate |
| POST | `/api/auth/login` | OAuth2 form login → JWT bearer token (HS256, 24 h) |
| GET | `/api/auth/me` | Current user from token |
| GET | `/api/jobs` | List discovered jobs (`limit`, `offset`) |
| GET | `/api/jobs/{id}` | Job detail (404 if unknown id) |
| POST | `/api/jobs/discover` | Pull from all enabled sources; dedup by (source, source_job_id) |
| POST | `/api/jobs/{id}/extract` | Run the Extraction Agent on one job (400 on unparseable output) |
| POST | `/api/jobs/extract-pending` | Batch-extract all jobs still in `discovered` |
| GET | `/api/profile/me` | Full profile (auto-created on first GET) |
| PUT | `/api/profile/me` | Replace full profile incl. educations, skills, experiences, projects, certifications, preferences |
| POST | `/api/resumes` | Upload PDF/DOCX (multipart `label` + `file`, ≤ `MAX_UPLOAD_MB`), text auto-extracted |
| GET | `/api/resumes` | List your resumes |
| GET | `/api/resumes/{id}` | Resume detail incl. parsed text |
| PUT | `/api/resumes/{id}/set-default` | Mark one resume as default |
| DELETE | `/api/resumes/{id}` | Delete resume row + file from disk |
| GET | `/api/applications` | List your applications (with match score/category/reasons) |
| POST | `/api/applications` | Create an application for a job (409 if one exists) |
| GET | `/api/applications/{id}` | Application detail |
| GET | `/api/applications/{id}/events` | Append-only status timeline |
| POST | `/api/applications/{id}/transition` | Change status — always appends a `status_events` row |
| POST | `/api/applications/{id}/match` | Run the Matching Agent for this application's job |
| GET | `/api/settings` | Non-secret runtime config (AI provider/model, source config, upload cap) |

All endpoints except `/api/health` and `/api/auth/*` require a bearer token.

## Configuration

All configuration is environment-driven (`.env`), defined once in
`backend/app/core/config.py` (pydantic-settings, cached):

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENV` | `development` | development / staging / production |
| `SECRET_KEY` | *required* | Signs JWT tokens |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `DATABASE_URL` | *required* | `postgresql+psycopg2://user:pass@host:port/db` |
| `REDIS_URL` | *required* | `redis://host:port/0` |
| `AI_PROVIDER` | `ollama` | ollama / gemini / groq / anthropic / openai |
| `AI_API_KEY` | – | Required for hosted providers (free tiers: gemini, groq) |
| `AI_MODEL` | `llama3.1` | Model for `complete_json()` |
| `AI_EMBED_MODEL` | `nomic-embed-text` | Model for `embed()` (768 dims = jobs.embedding) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint |
| `BROWSER_HEADLESS` | `true` | Playwright headless mode (later) |
| `JOB_SOURCE_CONFIG` | `{}` | JSON map of source name → bool; `{}` = all registered |
| `MAX_UPLOAD_MB` | `10` | Resume upload size cap |
| `UPLOAD_DIR` | `./uploads` | Local resume storage root |
| `NEXT_PUBLIC_API_URL` (frontend) | `http://localhost:8000` | Browser-reachable API base |

## Cost

Everything is free/open-source and self-hosted: Postgres, Redis, FastAPI,
Next.js, Playwright. The AI layer defaults to **Ollama** — fully local models,
no API key, no usage cost. `AI_PROVIDER` also supports `gemini` and `groq`
(adapters implemented; generous free tiers, only a free-signup API key).
`anthropic` is implemented too but needs a paid key and is not the default.

## Guiding principles

1. **Never fake discovery** — job data comes only from real, permitted sources.
2. **Never invent profile data** — the agent reasons over what you gave it.
3. **Never bypass protections** — no CAPTCHA/anti-bot circumvention, ever.
4. **Human approval is mandatory** — nothing is submitted without explicit sign-off
   (per-source opt-in auto-submission is the only future exception).
5. **Zero paid tooling by default** — free tiers and local models first.

## Docs

- [PRD.md](PRD.md) — product requirements, users, guardrails
- [Feature.md](Feature.md) — what exists vs what's planned
- [Todo.md](Todo.md) — prioritized, actionable work list
- [Implementation.md](Implementation.md) — how it's built, module by module
- [FutureUpdate.md](FutureUpdate.md) — roadmap and future updates
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — pipeline & data model notes

## Limitations

This system never invents profile data, never bypasses CAPTCHA/anti-bot
protections, and never submits an application without explicit user approval
unless automatic submission is deliberately enabled for a specific source.
Job sources are used strictly per their terms of service (e.g. Remotive
attribution + rate limits). Extraction/matching quality depends on the
selected model — local small models work but hosted free-tier models are
stronger. Frontend tokens live in localStorage (XSS-exposed by design for a
single-user local tool; httpOnly-cookie hardening is a v1.0 item).