# Feature Inventory

Legend: ✅ Implemented · 🟡 Partial (exists but incomplete) · 🔲 Planned (not started)

Last reviewed: 2026-09-21. Ground truth: the code in `backend/` — the frontend is an empty scaffold.

---

## 1. Accounts & authentication

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F1.1 | Register with email + password (bcrypt, min 8 chars) | ✅ | `app/api/auth.py`, `app/core/security.py` |
| F1.2 | Login (OAuth2 form) → JWT bearer token (HS256, 24 h) | ✅ | `app/api/auth.py`, `app/core/security.py` |
| F1.3 | Current-user resolution on protected routes | ✅ | `app/core/deps.py` |
| F1.4 | Refresh tokens / logout / session revocation | 🔲 | — |
| F1.5 | Password reset / email verification | 🔲 | — |

## 2. Profile

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F2.1 | One-to-one profile per user, auto-created on first GET | ✅ | `app/api/profile.py` |
| F2.2 | Personal info (name, phone, country, city, portfolio/GitHub/LinkedIn, other links) | ✅ | `app/models/profile.py` |
| F2.3 | Education entries (institution, degree, field, GPA optional) | ✅ | `app/models/profile.py` |
| F2.4 | Certifications (name, issuer, date, credential URL) | ✅ | `app/models/profile.py` |
| F2.5 | Skills with 10-category taxonomy (language, framework, library, database, cloud, AI/ML, NLP, DevOps, testing, other) | ✅ | `app/models/skill.py` |
| F2.6 | Experience entries (org, role, dates, achievements, skills used) | ✅ | `app/models/experience.py` |
| F2.7 | Projects (technologies, links, responsibilities, achievements) | ✅ | `app/models/project.py` |
| F2.8 | Matching preferences (roles, job/internship types, locations, work modes, salary/stipend floors, industries, keywords, excluded companies/roles, min match score) | ✅ stored | `app/models/preference.py` |
| F2.9 | Full-replace PUT save (children rebuilt atomically) | ✅ | `app/api/profile.py` |
| F2.10 | Profile completeness meter / validation hints | 🔲 | — |
| F2.11 | Import from LinkedIn / auto-fill from CV | 🔲 | — |

## 3. CV / Resume management

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F3.1 | Upload PDF/DOCX with label; extension whitelist + size cap (`MAX_UPLOAD_MB`) | ✅ | `app/api/resumes.py` |
| F3.2 | Local-disk storage `UPLOAD_DIR/<user_id>/<uuid>.<ext>` (no cloud, no paid storage) | ✅ | `app/api/resumes.py` |
| F3.3 | Text extraction (pypdf / python-docx); graceful null on scanned PDFs | ✅ | `app/services/resume_parser.py` |
| F3.4 | Multiple resumes, one default (`set-default`) | ✅ | `app/api/resumes.py` |
| F3.5 | Delete (DB row + file unlink) | ✅ | `app/api/resumes.py` |
| F3.6 | AI-structured extraction (skills/experience JSON) | 🔲 | `structured_data` column reserved |
| F3.7 | Per-job resume tailoring (variant generation) | 🔲 | — |
| F3.8 | Resume version history | 🔲 | — |

## 4. Job discovery

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F4.1 | `JobSource` adapter interface (search + details) | ✅ | `app/sources/base.py` |
| F4.2 | Source registry (decorator-based self-registration) | ✅ | `app/sources/registry.py` |
| F4.3 | Remotive adapter (official free API, attribution preserved, rate-limit aware, description cache) | ✅ | `app/sources/remotive.py` |
| F4.4 | Manual discovery trigger `POST /api/jobs/discover` | ✅ | `app/api/jobs.py`, `app/services/discovery.py` |
| F4.5 | Dedup by `(source, source_job_id)` — duplicates skipped | ✅ | `app/services/discovery.py` |
| F4.6 | Job listing/detail endpoints (response models, proper 404) | ✅ | `app/api/jobs.py`, `app/schemas/job.py` |
| F4.7 | Scheduled daily discovery (Celery beat) | 🔲 | no Celery app exists yet |
| F4.8 | Per-user search criteria in discovery | 🔲 | criteria dataclass exists |
| F4.9 | More sources (Greenhouse, Lever, Ashby, Arbeitnow, Adzuna, …) | 🔲 | pattern established |
| F4.10 | `content_hash` change detection on postings | 🔲 | column reserved |
| F4.11 | `JOB_SOURCE_CONFIG` toggle actually consulted | 🔲 | setting parsed nowhere yet |

## 5. Job extraction (Agent 2)

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F5.1 | Raw posting → structured fields (skills, salary, work mode, requirements, deadline) | 🔲 | `jobs` columns exist, unpopulated |
| F5.2 | JSON repair + schema validation of LLM output | 🔲 | `app/ai/base.py` references `json_repair.py` (not created) |
| F5.3 | Prompt templates for extraction | 🔲 | `app/prompts/` empty |

## 6. Matching (Agent 4)

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F6.1 | Rule-based eligibility (hard filters → `ineligible`) | 🔲 | preferences model ready |
| F6.2 | Structured skill comparison (required vs owned) | 🔲 | — |
| F6.3 | Semantic similarity (pgvector embeddings CV ↔ posting) | 🔲 | pgvector image + lib installed; no vector columns yet |
| F6.4 | LLM reasoning score (0–100) + category + reasons | 🔲 | columns exist on `applications` |
| F6.5 | Match explanation surface (UI/API) | 🔲 | — |

## 7. Application preparation (Agent 5)

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F7.1 | Resume selection (default/best) per application | 🔲 | FK `resume_id` exists |
| F7.2 | Cover letter drafting | 🔲 | column `cover_letter` exists |
| F7.3 | Question/answer drafting | 🔲 | column `answers_json` exists |

## 8. Human approval & submission

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F8.1 | `awaiting_approval` gate — nothing sends without explicit approval | 🔲 | status enum exists |
| F8.2 | Playwright browser agent (fills/submits, headless configurable) | 🔲 | `app/browser/` empty; playwright pinned |
| F8.3 | Never bypass CAPTCHA/anti-bot; `needs_user_action` fallback | 🔲 | by design |
| F8.4 | Opt-in auto-submission per source | 🔲 | — |

## 9. Tracking

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F9.1 | Application lifecycle model + append-only timeline | 🟡 models ✅, API/transitions 🔲 | `app/models/application.py` |
| F9.2 | Applications API (create/list/detail/update status) | 🔲 | — |
| F9.3 | Timeline UI | 🔲 | — |

## 10. Notifications

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F10.1 | New strong-match notifications | 🔲 | — |
| F10.2 | Status-change notifications | 🔲 | — |

## 11. Dashboard / frontend

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F11.1 | Next.js scaffold (app router, Tailwind) | 🔲 | `frontend/` dirs only — no package.json |
| F11.2 | Auth pages + token handling | 🔲 | — |
| F11.3 | Profile editor | 🔲 | — |
| F11.4 | Resume manager | 🔲 | — |
| F11.5 | Job feed + match list | 🔲 | — |
| F11.6 | Application tracker + timeline | 🔲 | — |
| F11.7 | Settings (AI provider, source toggles) | 🔲 | — |

## 12. Platform / ops

| ID | Feature | Status | Where |
|----|---------|--------|-------|
| F12.1 | Health endpoint | ✅ | `app/main.py` |
| F12.2 | docker-compose (postgres+pgvector, redis, backend, worker, scheduler, frontend) | 🟡 worker/scheduler wired (`app/tasks/celery_app.py`); frontend image unbuildable until Next.js is scaffolded | `docker-compose.yml` |
| F12.3 | Alembic migration setup | 🟡 env wired; no versions generated | `backend/alembic/` |
| F12.4 | AI provider abstraction + factory + Ollama adapter (JSON mode) | 🟡 factory works (`get_provider()`); only the ollama adapter exists so far | `app/ai/` |
| F12.5 | Celery worker + beat tasks | 🔲 | `app/tasks/` empty |
| F12.6 | Tests | 🔲 | `backend/tests/` empty |
| F12.7 | Git repo, .gitignore, LICENSE, CI, linting | 🔲 | not a git repo yet |

---

**Totals:** ✅ ~20 implemented · 🟡 5 partial · 🔲 ~25 planned — honest snapshot:
**foundation done; intelligence, workflow, and UI ahead.**