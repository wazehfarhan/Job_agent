# PRD — AI Job & Internship Application Agent

**Version:** 0.1 · **Status:** Draft · **Last reviewed:** 2026-09-21
**Related:** [Feature.md](Feature.md) · [Implementation.md](Implementation.md) · [FutureUpdate.md](FutureUpdate.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 1. Vision

A single user's AI hiring co-pilot: it watches permitted job boards, reads each
posting the way a recruiter would, compares it honestly against the user's real
profile and CV, drafts the application, and then **stops**. The user reviews
every detail and approves. Only then does the agent act — and everything it did
is recorded in an append-only timeline the user can audit at any time.

The system is **local-first** (self-hosted, local LLM by default), **free to
run** (no paid tools required), and **honest by construction** (it never
invents data, never fakes discoveries, and never bypasses site protections).

## 2. Problem

Applying to internships/jobs at scale is manual and repetitive:

- Finding relevant postings across boards takes hours per week.
- Judging fit (skills, location, salary, level) is error-prone and inconsistent.
- Tailoring resumes/cover letters per posting is slow.
- Tracking what was applied to, when, and what happened is usually a spreadsheet.

Existing tools are either paid SaaS where your data leaves your machine, or
aggressive auto-apply bots that spam applications without human judgment and
violate site terms. Neither is acceptable here.

## 3. Goals

| # | Goal | Measure |
|---|------|---------|
| G1 | Cut discovery time to minutes | Automated daily discovery; the user reviews only a matched shortlist |
| G2 | Honest, explainable match decisions | Every score ships with reasons (matched skills, gaps, rule outcomes) |
| G3 | Zero cost to run | All defaults free/self-hosted; no paid API required |
| G4 | Privacy | Profile/CV data stays on the user's machine by default (local Ollama) |
| G5 | Safety & compliance | No CAPTCHA bypass; permitted sources only; approval gate before submission |
| G6 | Full auditability | Append-only status timeline per application |

## 4. Non-goals (v1)

- Multi-tenant SaaS / teams / recruiters
- Guaranteeing interviews or offers
- Beating anti-bot systems (we refuse; if a site blocks automation, the user applies manually)
- Mass auto-apply without review
- Mobile native apps

## 5. Target user

**Primary:** the owner — a single self-hoster (student / new graduate) applying
to internships and entry-level tech roles, comfortable with Docker, who wants
their data local. Everything is designed single-user first.

**Secondary (future):** any privacy-conscious job seeker comfortable running containers.

## 6. Scope

**In scope:** job discovery via permitted sources; posting extraction into
structured data; deduplication; eligibility + match scoring with explanations;
resume/cover-letter/Q&A preparation; human approval workflow; permitted browser
automation for submission; status tracking with timeline; notifications;
dashboard UI.

**Out of scope (v1):** the §4 non-goals; scraping sources that forbid it;
reading the user's email for status detection (backlog idea).

## 7. User stories

| ID | Story | Priority | Status |
|----|-------|----------|--------|
| US-1 | As a user, I can register and log in so my data is mine. | P0 | ✅ |
| US-2 | As a user, I maintain one profile (education, skills, experience, projects, certifications, preferences) that drives all matching. | P0 | ✅ |
| US-3 | As a user, I upload multiple CVs (PDF/DOCX), pick a default, and their text is extracted for matching. | P0 | ✅ |
| US-4 | As a user, I trigger (and later schedule) discovery so new postings land in my job DB. | P0 | 🟡 manual only |
| US-5 | As a user, each posting is parsed into structured fields (skills, salary, work mode, deadlines) I can trust. | P1 | 🔲 |
| US-6 | As a user, I see a ranked shortlist (strong / possible / weak / ineligible) with reasons. | P1 | 🔲 |
| US-7 | As a user, I get a prepared application (default resume, cover letter draft, question answers) per job. | P1 | 🔲 |
| US-8 | As a user, I explicitly approve an application before anything is submitted. | P0 | 🔲 |
| US-9 | As a user, the agent submits via the browser only within site rules, pausing when blocked. | P2 | 🔲 |
| US-10 | As a user, I see every application's status and full history timeline. | P1 | 🔲 |
| US-11 | As a user, I get notified of new strong matches and status changes. | P2 | 🔲 |

## 8. Functional requirements

### 8.1 Accounts & auth
- **FR-1** Email+password registration; bcrypt hashing; min length 8. ✅
- **FR-2** JWT bearer auth (HS256, 24 h expiry) on every protected endpoint. ✅
- **FR-3** Per-user data isolation on all objects (profile, resumes, applications). ✅ (enforced per endpoint)

### 8.2 Profile
- **FR-4** One profile per user: personal info, educations, certifications, skills (categorized), experiences, projects, preferences. ✅
- **FR-5** Preferences capture target roles, job/internship types, locations, work modes, min salary/stipend, industries, keywords, exclusions, min match score — the contract the Matching Agent consumes. ✅ (stored; matching TBD)
- **FR-6** Profile save atomically replaces child collections. ✅

### 8.3 CV / Resume
- **FR-7** Upload PDF/DOCX only; size capped by `MAX_UPLOAD_MB`; stored locally under `UPLOAD_DIR/<user_id>/` with UUID filenames. ✅
- **FR-8** Text extracted locally (pypdf / python-docx); if extraction fails (scanned PDF), the file is stored with null text — never guessed. ✅
- **FR-9** Multiple resumes; exactly one default. ✅
- **FR-10** (later) AI-structured extraction into skills/experience/projects. 🔲 (column `structured_data` reserved)

### 8.4 Discovery
- **FR-11** `JobSource` adapter interface (`search_jobs`, `get_job_details`); adapters self-register; never fake results. ✅
- **FR-12** Dedup on `(source, source_job_id)`; duplicates skipped, never re-inserted. ✅
- **FR-13** Respect each source's terms: attribution preserved, rate limits honored (Remotive ≤ ~4×/day). ✅
- **FR-14** Scheduled discovery (Celery beat, ~daily). 🔲
- **FR-15** Per-user criteria (keywords/types) applied to discovery. 🔲

### 8.5 Extraction
- **FR-16** Fetch raw posting content and extract into `jobs` structured fields: company, title, description, location, work_mode, employment_type, salary, required/preferred skills, experience/education requirements, deadline, application URL. 🔲
- **FR-17** LLM output validated/normalized (JSON repair) before persisting; unparseable postings are flagged, never guessed. 🔲
- **FR-18** Content hash to detect posting changes. 🔲 (column reserved)

### 8.6 Matching
- **FR-19** Rule-based eligibility first (location/work-mode/salary/type/exclusions) → hard filter, category `ineligible`. 🔲
- **FR-20** Structured skill comparison (required vs owned, exact + synonyms). 🔲
- **FR-21** Semantic similarity via pgvector embeddings of CV vs posting. 🔲
- **FR-22** LLM reasoning produces score 0–100, category (strong/possible/weak/ineligible), and human-readable reasons; rules + structured checks always run before/alongside the LLM. 🔲
- **FR-23** Score, category, and reasons persisted on the application. 🔲 (columns exist)

### 8.7 Application preparation
- **FR-24** Select default (or best) resume; draft a cover letter from profile + posting; draft answers for known application questions; all stored on the application row. 🔲

### 8.8 Approval & submission
- **FR-25** Application enters `awaiting_approval`; nothing is sent without explicit approval (`approved` → `submitting`). 🔲
- **FR-26** Browser agent (Playwright) fills and submits; never bypasses CAPTCHA/anti-bot; on any blocker → `needs_user_action`. 🔲
- **FR-27** Auto-submission only if explicitly enabled for that source in config, never the default. 🔲

### 8.9 Tracking
- **FR-28** `ApplicationStatus` lifecycle: discovered → analyzing → matched → preparing → awaiting_approval → approved → submitting → applied → interview / rejected / withdrawn / failed / needs_user_action. 🔲 (enum exists; transitions not yet driven)
- **FR-29** Every transition appends a `status_events` row (append-only; history is never mutated). 🔲 (model exists; no API)

### 8.10 Notifications
- **FR-30** Notify on new strong matches and on status changes (channel TBD: local webhook / SMTP email). 🔲

### 8.11 Dashboard
- **FR-31** Pages: login/register, profile editor, resume manager, job feed with match filters, application detail with timeline, settings (sources, AI provider). 🔲

## 9. Non-functional requirements

| # | Requirement |
|---|-------------|
| NFR-1 | **Cost:** runs fully free — local Ollama default; hosted providers limited to free tiers (gemini/groq). |
| NFR-2 | **Privacy:** profile/CV never leaves the machine by default; uploads on local disk; no third-party storage. |
| NFR-3 | **Security:** bcrypt + JWT; uploaded files stored under random UUID names (path-traversal safe); size/type validated; secrets only via env. |
| NFR-4 | **Honesty:** never fabricate job or profile data; failed parses/extractions surface as failures. |
| NFR-5 | **Compliance:** only permitted sources; honor ToS (attribution, rate limits); never bypass bot protections. |
| NFR-6 | **Auditability:** append-only application timeline. |
| NFR-7 | **Reliability:** request-scoped DB sessions; dedup idempotency; a failed source pull must not corrupt the job DB. |
| NFR-8 | **Testability:** each pipeline stage is a separate, unit-testable component (tests TBD — T3.4). |

## 10. Constraints & guardrails (non-negotiable)

1. No invented data — profile fields come from the user; job fields come from sources.
2. No fake discovery — a source is enabled only when a real adapter is implemented and configured.
3. No CAPTCHA/anti-bot bypass.
4. No submission without explicit human approval (per application).
5. No paid tools required by default.

## 11. Success metrics

- ≥ 90% of postings deduped correctly (no duplicate rows for the same posting).
- Extraction fills ≥ 8 structured fields for ≥ 80% of postings.
- User reviews < 20 postings to find ≥ 5 strong matches/week (with sane preferences).
- 100% of submissions preceded by an `awaiting_approval → approved` event.
- Zero paid-service dependencies in the default configuration.

## 12. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Source API changes / rate limits | Isolated adapters; conservative scheduling; per-source config toggles |
| Local model too weak for extraction | Provider abstraction → swap to free-tier hosted models via env |
| Sites block Playwright | Never bypass; mark `needs_user_action`; user applies manually |
| LLM hallucination in extraction/matching | JSON repair + schema validation; rule-based checks first; never trust the LLM alone |
| Single-user scope creep | Keep per-user FKs; defer multi-user features explicitly |

## 13. Release plan

Phased — see [FutureUpdate.md](FutureUpdate.md). Current phase: **Phase 2 — data
foundation** (auth, profile, CV, discovery done; extraction next).