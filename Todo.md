# TODO

Prioritized and actionable. **P0** = blocks running the system · **P1** = next
core value · **P2** = user experience · **P3** = automation/ops · **P4** = hygiene.
Each item lists what to change and how to verify.

---

## P0 — Blocking (fix before anything else)

> T0.1 and T0.3–T0.7 completed 2026-09-21. T0.2 remains open — it needs a
> running Postgres to autogenerate against (no Docker on the dev machine);
> exact commands are in the item below.

- [x] **T0.1 Fix the import error that prevents boot.** `app/api/resumes.py` does
      `from app.schemas.resume import ResumeDetailOut, ResumeOut`, but
      `app/schemas/resume.py` does not exist — the schemas currently live
      (misplaced) in `app/services/resume.py`. `app.main` → routers → ModuleNotFoundError.
      → Move that module to `backend/app/schemas/resume.py`; delete `app/services/resume.py`.
      **Verify:** `uvicorn app.main:app` starts; `/docs` renders.
- [ ] **T0.2 Create the initial Alembic migration.** `alembic/versions/` is empty, so
      no tables exist and every DB endpoint will 500.
      → `alembic revision --autogenerate -m "initial schema"` (DB must be up); include
      `CREATE EXTENSION IF NOT EXISTS vector;` for pgvector.
      **Verify:** `alembic upgrade head` creates all 12 tables.
- [x] **T0.3 Fix docker-compose worker/scheduler.** They run
      `celery -A app.tasks.celery_app …` but no Celery app module exists → crash-loop.
      → Create `backend/app/tasks/celery_app.py` (broker + result backend from `REDIS_URL`).
      **Verify:** `docker compose up worker scheduler` stay running.
- [x] **T0.4 Compose networking.** `.env.example` points `DATABASE_URL`/`REDIS_URL` at
      `localhost`, which is unreachable from inside the compose network.
      → Document compose-specific values (`postgres`/`redis` hostnames) or ship
      `.env.docker.example`.
      **Verify:** full `docker compose up` stack talks to its own DB/Redis.
- [x] **T0.5 Implement `app/ai/factory.py`.** It is empty, so `AI_PROVIDER` is inert.
      → `get_provider() -> AIProvider` switching on settings; wire the existing
      Ollama adapter now; raise a clear error for unimplemented providers.
      **Verify:** unit test returns `OllamaProvider` for default settings.
- [x] **T0.6 Align `.env.example` with code.** Example sets `AI_PROVIDER=anthropic`,
      `AI_MODEL=claude-sonnet-4-6`; code defaults are `ollama` / `llama3.1`.
      → Change the example to `AI_PROVIDER=ollama` (document gemini/groq as free-tier
      alternatives) or justify keeping anthropic.
- [x] **T0.7 Proper 404 + response models on jobs endpoints.** `GET /api/jobs/{id}`
      returns HTTP 200 `{"error":"not_found"}` (resumes correctly raise 404); jobs
      list/detail return raw ORM objects without `response_model`.
      → Raise 404; add `JobOut` schema.

## P1 — Core pipeline (the actual product)

- [ ] **T1.1 Extraction agent** (`app/agents/extraction.py` + prompts in `app/prompts/`):
      fetch raw description via `source.get_job_details`, LLM → structured fields
      (work_mode, employment_type, salary range/currency, required/preferred skills,
      experience/education requirements, deadline, application_url); JSON-repair +
      validate before persisting; transition `jobs.status` `discovered → extracted`;
      flag unparseable postings instead of guessing.
- [ ] **T1.2 JSON repair service** `app/services/json_repair.py` (already referenced by
      `app/ai/base.py` docstring): strip preamble, fix common JSON faults, validate
      against Pydantic schemas.
- [ ] **T1.3 Embeddings + pgvector:** add `embedding vector(N)` to `jobs` (and a profile
      text vector); generate via provider (Ollama embeddings first); index for cosine search.
- [ ] **T1.4 Matching agent** (`app/agents/matching.py`): rule-based eligibility →
      structured skill comparison → cosine similarity → LLM score + reasons;
      persist `match_score`, `match_category`; create `Application(discovered)` +
      first `StatusEvent`.
- [ ] **T1.5 Applications API:** create/list/detail; status-transition endpoint that
      appends a `StatusEvent` on every change (append-only rule enforced in one place).
- [ ] **T1.6 Provider adapters for gemini/groq** behind the factory (free tiers; use
      httpx — no SDKs are pinned for them); optional `anthropic` adapter (dep already in
      requirements.txt).
- [ ] **T1.7 `content_hash`** computed at extraction (sha256 of normalized description)
      for posting-change detection.
- [ ] **T1.8 Honor `JOB_SOURCE_CONFIG`** in `registry.get_enabled_sources()` (currently
      parsed nowhere) — enable/disable sources per configuration.

## P2 — Frontend

- [ ] **T2.1** Scaffold Next.js (TypeScript + Tailwind + app router) in `frontend/`;
      `package.json` does not exist today, so the compose `frontend` image cannot build.
- [ ] **T2.2** Auth pages (register/login/logout) + token storage + API client that
      sends the bearer header.
- [ ] **T2.3** Profile editor (one form → `PUT /api/profile/me` full-replace semantics).
- [ ] **T2.4** Resume manager (upload/list/set-default/delete; show parse status incl.
      the scanned-PDF null case).
- [ ] **T2.5** Job feed (list/detail, "Discover now" button → `POST /api/jobs/discover`).
- [ ] **T2.6** Applications tracker (status board + timeline view from `status_events`).
- [ ] **T2.7** Settings page (AI provider/model, source toggles → `JOB_SOURCE_CONFIG`).

## P3 — Automation & ops

- [ ] **T3.1** Celery beat schedule: daily discovery (respecting Remotive ≤ ~4×/day) +
      periodic extraction/matching sweeps.
- [ ] **T3.2** Playwright browser agent with `needs_user_action` fallback; screenshot
      evidence per submission step; `BROWSER_HEADLESS` honored.
- [ ] **T3.3** Notifications (new strong matches; status changes) — start with local
      webhook/email.
- [ ] **T3.4** Backend tests: auth flows, profile round-trip, resume upload limits,
      dedup idempotency, source adapters (mock HTTP).
- [ ] **T3.5** CI (GitHub Actions): ruff + pytest on backend; typecheck/build on frontend.
- [ ] **T3.6** Central per-source rate-limit ledger (no adapter may exceed its quota).

## P4 — Hygiene

- [x] **T4.1** `git init` + initial commit; add `.gitignore` (`.env`, `uploads/`,
      `__pycache__/`, `node_modules/`, `.venv/`, `.DS_Store`). *(done 2026-09-21 — initial commit on `main`)*
- [ ] **T4.2** Add `app/ai/providers/__init__.py`; re-export models in
      `app/models/__init__.py` (currently empty).
- [ ] **T4.3** CORS origins from env (`ALLOWED_ORIGINS`) instead of hardcoded
      `http://localhost:3000`.
- [ ] **T4.4** Keep docs honest: update Feature.md statuses and Todo.md checkboxes
      at the end of every phase.