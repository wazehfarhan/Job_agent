# TODO

Prioritized and actionable. **P0** = blocks running the system · **P1** = next
core value · **P2** = user experience · **P3** = automation/ops · **P4** = hygiene.
Each item lists what to change and how to verify.

---

## P0 — Blocking (fix before anything else) — ✅ COMPLETE

> All seven P0 items are done. T0.2's migration (`alembic/versions/0001_initial_schema.py`)
> is hand-written to match the models exactly — verify it once against a live
> Postgres (`docker compose up postgres redis` then `alembic upgrade head`),
> which is the only part that couldn't run on the dev machine (no Docker).

- [x] **T0.1** Resume schemas moved to `app/schemas/resume.py` (boot restored). ✅
- [x] **T0.2** Initial Alembic migration written (12 tables, 5 enum types, indexes, pgvector extension + hnsw index). Verify with a live DB. ✅
- [x] **T0.3** `app/tasks/celery_app.py` created — compose worker/scheduler no longer crash-loop. ✅
- [x] **T0.4** `.env.docker.example` with compose-correct `postgres`/`redis` hostnames. ✅
- [x] **T0.5** `app/ai/factory.py` implemented (`get_provider()`; fails loudly for unimplemented providers). ✅
- [x] **T0.6** `.env.example` aligned with code defaults (`ollama` / `llama3.1`). ✅
- [x] **T0.7** Jobs endpoints: response models + proper 404. ✅

## P1 — Core pipeline — ✅ COMPLETE

- [x] **T1.1 Extraction agent** (`app/agents/extraction.py` + `app/prompts/extraction.py`):
      fetch raw description via the source adapter, LLM → structured fields,
      JSON-repair + validate, `discovered → extracted`; batch + single endpoints.
- [x] **T1.2 JSON repair service** (`app/services/json_repair.py`): fence/preamble
      stripping, string-aware brace matching, trailing-comma fix, `parse_model()`.
- [x] **T1.3 Embeddings + pgvector**: `jobs.embedding` Vector(768) + hnsw cosine index;
      `AIProvider.embed()` (Ollama `/api/embeddings`, `AI_EMBED_MODEL=nomic-embed-text`).
- [x] **T1.4 Matching agent** (`app/agents/matching.py`): rule eligibility →
      skill comparison → cosine similarity → LLM score/reasons (heuristic fallback);
      persists `match_score`, `match_category`, `match_reasons`; creates the
      application + append-only `StatusEvent`s.
- [x] **T1.5 Applications API** (`app/api/applications.py`): create (409 on
      duplicate), list/detail, `POST /{id}/transition` (append-only events),
      `POST /{id}/match`, `GET /{id}/events` timeline.
- [x] **T1.6 Provider adapters**: gemini + groq (httpx, free tiers), anthropic
      (pinned SDK); factory fail-fast on missing `AI_API_KEY`.
- [x] **T1.7 `content_hash`** computed at discovery and refreshed at extraction
      (sha256 of normalized description) for change detection.
- [x] **T1.8 `JOB_SOURCE_CONFIG`** honored by `registry.get_enabled_sources()`;
      `get_source(name)` for extraction; per-source failure isolation in discovery.

## P2 — Frontend — ✅ CODE COMPLETE (needs `npm install` to run)

- [x] **T2.1** Hand-written Next.js 14 scaffold (App Router, TypeScript, Tailwind):
      `package.json` / `tsconfig.json` / `tailwind.config.ts` / `postcss.config.mjs` /
      `next.config.mjs`, dev-parity `Dockerfile`, `.gitignore`, `.env.local.example`.
      No lockfile committed — run `npm install` once before `npm run dev`.
- [x] **T2.2** Auth: login/register page (one form, mode toggle), token in
      localStorage, `lib/api.ts` typed client (bearer header, 401 → auto-logout +
      redirect, FormData/URLSearchParams aware), `useRequireAuth` guard hook.
- [x] **T2.3** Profile editor: personal, links, education, certifications, skills
      (10-category select), experience, projects, matching preferences →
      `PUT /api/profile/me` full-replace; null/number/list conversions on save.
- [x] **T2.4** Resume manager: upload (label + file), list, set-default, delete,
      expandable parsed-text view (surfaces the scanned-PDF null case).
- [x] **T2.5** Job feed: Discover now / Extract pending; per-job Extract and
      Apply (track) → creates an application; salary/skills/description display.
- [x] **T2.6** Applications tracker: score/category badges + reasons list, Match
      button, inline status transition, detail page with note-form transitions and
      the full append-only timeline.
- [x] **T2.7** Settings page: backend health + read-only runtime config via the new
      `GET /api/settings` endpoint (never exposes secrets); source-enablement docs.

## P3 — Automation & ops

- [x] **T3.1** Celery beat schedule: daily discovery (respecting Remotive ≤ ~4×/day) +
      hourly extraction sweep + 2-hourly matching sweep — `app/tasks/pipeline.py`
      + `beat_schedule` in `app/tasks/celery_app.py`. *(needs a live worker run to verify)*
- [x] **T3.2** Browser Agent written (`app/browser/agent.py`): approval gate
      re-checked at agent level, CAPTCHA/anti-bot detection → `needs_user_action`,
      per-step screenshots under `BROWSER_EVIDENCE_DIR`, heuristic answer matching
      from `answers_json` + cover letter (never invents), `BROWSER_AUTO_SUBMIT=false`
      default (fills + evidences + hands back to the human). Needs a live run to verify.
- [x] **T3.3** Notifications (`app/services/notifications.py`): optional webhook +
      SMTP email channels, fire-and-forget (never breaks the caller); wired into
      strong matches, status transitions, and browser-submission outcomes.
      Log-only when unconfigured.
- [x] **T3.4** Pure-unit test suite written (`backend/tests/`: json_repair, matching
      logic, discovery content_hash, registry config, extraction helpers, security —
      ~35 tests, no DB/network/LLM needed). DB-backed + adapter tests with mocked
      HTTP still to add; execute in Docker/CI (needs Python 3.12 deps — this dev
      machine only has 3.9).
- [ ] **T3.5** CI (GitHub Actions): ruff + pytest on backend; typecheck/build on frontend.
- [ ] **T3.6** Central per-source rate-limit ledger (no adapter may exceed its quota).

## P4 — Hygiene

- [x] **T4.1** `git init` + initial commit; add `.gitignore` (`.env`, `uploads/`,
      `__pycache__/`, `node_modules/`, `.venv/`, `.DS_Store`).
- [x] **T4.2** `app/ai/providers/__init__.py` + model re-exports in
      `app/models/__init__.py` (both done during the rebuild).
- [x] **T4.3** CORS origins from env (`ALLOWED_ORIGINS`) instead of hardcoded
      `http://localhost:3000`.
- [ ] **T4.4** Keep docs honest: update Feature.md statuses and Todo.md checkboxes
      at the end of every phase. *(ongoing — maintained through the v0.4 release)*