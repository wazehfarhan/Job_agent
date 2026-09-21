# Future Updates — Roadmap & Backlog

Where the project goes next. Phases follow the development order in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
**Current position: v0.2–v0.4 shipped** (infrastructure, extraction, matching).
Next up: **v0.5 — application preparation + approval flow**, then the frontend.

---

## Milestone map

```
v0.2  Make it run            → P0 fixes (boot, migrations, Celery app, AI factory)  ✅ SHIPPED
v0.3  Make it understand     → Extraction agent + embeddings (pgvector)              ✅ SHIPPED
v0.4  Make it judge          → Matching agent (rules + skills + similarity + LLM)    ✅ SHIPPED
v0.5  Make it act (safely)   → Applications, preparation, approval gate, tracking API
v0.6  Make it visible        → Frontend dashboard
v0.7  Make it submit         → Playwright browser agent (permitted automation only)
v0.8  Make it autonomous     → Scheduler, notifications, real workflows
v1.0  Make it trustworthy    → Tests, security review, E2E, ops docs
```

## v0.2 — Make it run ✅ SHIPPED (2026-09-21)

| Change | Status |
|--------|--------|
| Resume schemas moved to `app/schemas/resume.py` (boot blocker) | ✅ |
| Initial Alembic migration `0001_initial_schema.py` (hand-written; verify against live Postgres) | ✅ written |
| `app/tasks/celery_app.py` (compose worker/scheduler) | ✅ |
| `.env.docker.example` with compose-correct hostnames | ✅ |
| AI factory + provider switch (`get_provider()`) | ✅ |
| Config alignment, proper 404s + response models | ✅ |

## v0.3 — Make it understand ✅ SHIPPED (2026-09-21)

- **Extraction agent** (`app/agents/extraction.py`): raw description → structured
  `jobs` fields; single + batch endpoints; `content_hash` refreshed on extraction.
- **JSON repair** (`app/services/json_repair.py`): fence stripping, balanced-brace
  extraction, trailing-comma fix; failures surface, never guessed around.
- **Embeddings**: `jobs.embedding` Vector(768) + hnsw index; `AIProvider.embed()`
  (Ollama first); generated best-effort during extraction.
- **Exit criteria met:** structured fields populated without hallucination
  (validation at every step); embeddings optional, never blocking.

## v0.4 — Make it judge ✅ SHIPPED (2026-09-21)

- Matching chain: hard rule eligibility → structured skill comparison →
  cosine similarity → LLM score + reasons; heuristic fallback when the LLM or
  embedding model is unavailable.
- User preferences applied (work modes, job types, salary floor, exclusions, locations).
- Persisted explanation object (`match_reasons[]`) exposed via the Applications API.

## v0.5 — Make it act (safely) — NEXT

- Preparation agent: default-resume selection, cover-letter draft, question
  answers (columns already exist: `resume_id`, `cover_letter`, `answers_json`).
- Approval gate flow: `preparing → awaiting_approval` blocks submission;
  explicit approve/reject endpoints drive `approved`/`needs_user_action`.
- (Applications + transition + timeline API already shipped in v0.4.)

## v0.6 — Make it visible ✅ CODE SHIPPED (2026-09-21)

- Next.js 14 frontend written: dashboard, login/register, profile editor,
  resume manager, job feed (discover/extract/apply), applications tracker with
  timeline + reasons, settings page. Backend gained `GET /api/settings`
  (non-secret runtime config).
- Remaining for v0.6 closure: `npm install && npm run dev`, then walk the first
  end-to-end manual flow (upload CV → discover → extract → match → review
  reasons → track status) against a live backend and fix what shakes out.

## v0.7 — Make it submit

- Playwright browser agent: navigates application forms, fills from prepared
  answers, screenshots each step, honors `BROWSER_HEADLESS`.
- Hard rules: never bypass CAPTCHA/anti-bot; `needs_user_action` on blockers;
  per-source opt-in auto-submission only (never default).

## v0.8 — Make it autonomous

- Celery beat schedules (daily discovery, periodic extraction/matching sweeps).
- Notifications (strong matches, status changes) — local webhook/email first.
- Multi-source discovery with a central per-source rate-limit ledger.

## v1.0 — Make it trustworthy

- Backend test suite (auth, profile, resume limits, dedup idempotency, adapters
  with mocked HTTP, json_repair, matching heuristics).
- Security review: token handling, upload safety, SSRF checks on source URLs, secret hygiene.
- E2E test of the full pipeline against a sandbox source; ops runbook + backup/restore docs.

---

## Backlog (ideas beyond v1.0)

| Idea | Value | Risk / Notes |
|------|-------|--------------|
| More sources: Greenhouse/Lever/Ashby public boards, Arbeitnow, Adzuna free tier, "Who's hiring" parser | Discovery breadth | Each needs its own ToS review before an adapter is written |
| Resume tailoring per job (variant generation + diff view) | Higher match quality | Guardrail: never invent experience; user approves every variant |
| Interview prep module (company research, question bank from the posting) | Extends value post-application | Local-model latency; keep optional |
| Email ingestion for status parsing (confirmations, interview invites) | Auto-tracking | Local IMAP only; privacy-sensitive |
| Calendar integration (deadlines, interviews) | Time management | Read-only first |
| Multi-user mode (everything is already per-user FK'd) | Broader audience | Auth hardening + rate isolation required first |
| Production compose (TLS reverse proxy, baked images) | Real deployments | Non-goal while single-user local |
| S3-compatible storage option for resumes | Portability | Optional, never required (cost rule) |
| Mobile PWA | Convenience | After the dashboard exists |
| Metrics dashboard (funnel: discovered → matched → applied → interview) | Insight | Needs status-event data first |

## Explicitly rejected (do not build)

- CAPTCHA/anti-bot bypass of any kind
- Fake/synthetic job discovery to "demo" the pipeline
- Auto-submit without approval as a default
- Paid-only tooling as a hard dependency