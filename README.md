# AI Job & Internship Application Agent

A self-hosted, personal AI agent that discovers job and internship postings from
permitted sources, matches them against your profile and CV, explains the match,
prepares application materials, and tracks every application's status — always
pausing for your explicit approval before anything is ever submitted.

> **Status: early development (Phase 2 of the roadmap).** Auth, profile, CV
> upload/parsing, job storage, the source abstraction, and the first real
> source (Remotive) are implemented. Extraction, matching, application prep,
> browser automation, tracking UI, notifications, and the frontend are **not
> built yet**. See [FutureUpdate.md](FutureUpdate.md) for the roadmap and
> [Todo.md](Todo.md) for the current prioritized work list (the P0 code fixes
> were applied 2026-09-21; the first Alembic migration — T0.2 — is still open).

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
| Frontend | Next.js / React / TypeScript / Tailwind *(empty scaffold — not built yet)* |
| API | FastAPI + Pydantic v2 (Python 3.12) |
| Database | PostgreSQL 16 + pgvector |
| Queue | Redis 7 + Celery (worker + beat) |
| Parsing | pypdf (PDF), python-docx (DOCX) |
| Automation | Playwright *(planned — permitted automation only)* |
| AI | Provider-agnostic: local Ollama by default; gemini/groq free tiers; anthropic/openai adapters supported but not default |

## Repository layout

```
job-agent/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers: auth, jobs, profile, resumes
│   │   ├── core/         # config, database, security, deps, redis
│   │   ├── models/       # SQLAlchemy ORM models (12 tables)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # discovery (dedup), resume parsing
│   │   ├── sources/      # JobSource adapters: base, registry, remotive
│   │   ├── ai/           # AIProvider abstraction + Ollama adapter
│   │   ├── agents/       # (empty) pipeline agents land here
│   │   ├── prompts/      # (empty) LLM prompt templates land here
│   │   ├── browser/      # (empty) Playwright automation lands here
│   │   └── tasks/        # (empty) Celery app/tasks land here
│   ├── alembic/          # migration setup (no versions generated yet)
│   ├── tests/            # (empty)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # (empty scaffold — Next.js not initialized yet)
├── infrastructure/       # (empty — deployment/, docker/)
├── scripts/              # (empty)
├── docs/ARCHITECTURE.md  # pipeline + data model notes
├── docker-compose.yml    # postgres, redis, backend, worker, scheduler, frontend
├── .env.example          # local-run defaults (ollama, localhost services)
├── .env.docker.example   # compose-run variant (postgres/redis service hostnames)
├── PRD.md                # product requirements
├── Feature.md            # feature inventory (implemented vs planned)
├── Todo.md               # prioritized work list
├── Implementation.md     # how the system is built today
└── FutureUpdate.md       # roadmap & backlog
```

## Quick start (Docker)

```bash
cp .env.example .env      # then set SECRET_KEY (any long random string)
docker compose up
```

- Backend: http://localhost:8000 (interactive docs at `/docs`)
- Frontend: http://localhost:3000 *(not built yet)*
- Postgres: localhost:5432 (job_agent / job_agent) · Redis: localhost:6379

> **Heads-up:** the compose `frontend` image cannot build until Next.js is
> scaffolded (Todo T2.1), and the API needs its first Alembic migration before
> DB-backed endpoints work (Todo T0.2 — run `alembic revision
> --autogenerate -m "initial schema"` against a live Postgres, then
> `alembic upgrade head`). Everything else from the original P0 list is fixed.

## Running the backend locally

Requires **Python 3.12** (the code uses `X | None` syntax and SQLAlchemy 2.0
typed mappings; the system Python 3.9 is not sufficient):

```bash
docker compose up postgres redis          # infra only
cp .env.example .env                      # fill in SECRET_KEY
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                      # once the first migration exists (Todo T0.2)
uvicorn app.main:app --reload
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
| GET | `/api/profile/me` | Full profile (auto-created on first GET) |
| PUT | `/api/profile/me` | Replace full profile incl. educations, skills, experiences, projects, certifications, preferences |
| POST | `/api/resumes` | Upload PDF/DOCX (multipart `label` + `file`, ≤ `MAX_UPLOAD_MB`), text auto-extracted |
| GET | `/api/resumes` | List your resumes |
| GET | `/api/resumes/{id}` | Resume detail incl. parsed text |
| PUT | `/api/resumes/{id}/set-default` | Mark one resume as default |
| DELETE | `/api/resumes/{id}` | Delete resume row + file from disk |

All endpoints except `/api/health` and `/api/auth/*` require a bearer token.

## Configuration

All configuration is environment-driven (`.env`), defined once in
`backend/app/core/config.py` (pydantic-settings, cached):

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENV` | `development` | development / staging / production |
| `SECRET_KEY` | *required* | Signs JWT tokens |
| `DATABASE_URL` | *required* | `postgresql+psycopg2://user:pass@host:port/db` |
| `REDIS_URL` | *required* | `redis://host:port/0` |
| `AI_PROVIDER` | `ollama` | ollama / gemini / groq / anthropic / openai |
| `AI_API_KEY` | – | Only needed for hosted providers |
| `AI_MODEL` | `llama3.1` | Model name for the selected provider |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint |
| `BROWSER_HEADLESS` | `true` | Playwright headless mode (later) |
| `JOB_SOURCE_CONFIG` | `{}` | JSON toggling which sources are enabled *(not yet consulted — T1.8)* |
| `MAX_UPLOAD_MB` | `10` | Resume upload size cap |
| `UPLOAD_DIR` | `./uploads` | Local resume storage root |

## Cost

Everything is free/open-source and self-hosted: Postgres, Redis, FastAPI,
Next.js, Playwright. The AI layer defaults to **Ollama** — fully local models,
no API key, no usage cost. `AI_PROVIDER` also supports `gemini` and `groq`
(generous free tiers; only a free-signup API key). `anthropic`/`openai`
adapters are supported by the abstraction but need a paid key and are not the
default.

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
attribution + rate limits).
