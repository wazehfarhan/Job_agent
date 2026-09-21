# Future Updates — Roadmap & Backlog

Where the project goes after the current foundation. Phases follow the
development order in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
**Current position: end of Phase 2** (auth, profile, CV, discovery done;
extraction next).

---

## Milestone map

```
v0.2  Make it run            → P0 fixes (boot, migrations, Celery module, AI factory)
v0.3  Make it understand     → Extraction agent + embeddings (pgvector)
v0.4  Make it judge          → Matching agent (rules + skills + similarity + LLM reasons)
v0.5  Make it act (safely)   → Applications, preparation, approval gate, tracking API
v0.6  Make it visible        → Frontend dashboard
v0.7  Make it submit         → Playwright browser agent (permitted automation only)
v0.8  Make it autonomous     → Scheduler, notifications, real workflows
v1.0  Make it trustworthy    → Tests, security review, E2E, ops docs
```

## v0.2 — Make it run (next)

> Status 2026-09-21: T0.1 and T0.3–T0.7 are shipped; **T0.2 (initial Alembic
> migration) remains** — it needs a live Postgres to autogenerate against.

| Change | Why | Depends on |
|--------|-----|------------|
| Move resume schemas to `app/schemas/resume.py` (T0.1) | Backend cannot boot otherwise | — |
| Initial Alembic migration + pgvector extension (T0.2) | No tables exist | DB up |
| `app/tasks/celery_app.py` (T0.3) | compose worker/scheduler crash-loop | Redis |
| Compose-correct `.env` values (T0.4) | `localhost` DB/Redis URLs break in compose | — |
| AI factory + provider switch (T0.5) | `AI_PROVIDER` currently inert | — |
| Config/doc alignment, proper 404s (T0.6, T0.7) | Predictable API | — |

## v0.3 — Make it understand

- **Extraction agent** (`app/agents/`): raw description → structured `jobs` fields;
  JSON repair service (`app/services/json_repair.py`, already referenced by
  `app/ai/base.py`); prompt templates in `app/prompts/`.
- **Embeddings**: `vector` column on `jobs` + profile text vector; Ollama embeddings first.
- **`content_hash`** change detection; re-extraction policy for edited postings.
- **Exit criteria:** ≥ 80% of discovered postings have ≥ 8 structured fields populated;
  zero hallucinated fields reach the DB unvalidated.

## v0.4 — Make it judge

- Matching agent chain: hard rule eligibility → structured skill comparison →
  cosine similarity → LLM score + reasons; categories strong / possible / weak / ineligible.
- User preferences applied (already modeled in `preferences`).
- Persisted explanation object ("why this score") for the future UI.

## v0.5 — Make it act (safely)

- Applications API + a single status-transition service that appends a `StatusEvent`
  for every change (append-only rule enforced in one place).
- Preparation agent: default-resume selection, cover-letter draft, question answers.
- Approval gate: `awaiting_approval` blocks submission; explicit approve/reject endpoints.

## v0.6 — Make it visible

- Next.js scaffold + auth pages, profile editor, resume manager, job feed,
  tracker timeline, settings.
- First end-to-end manual flow: upload CV → discover → review matches →
  approve → (manual apply) → track status.

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

- Backend test suite (auth, profile, resume limits, dedup idempotency, adapters with mocked HTTP).
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