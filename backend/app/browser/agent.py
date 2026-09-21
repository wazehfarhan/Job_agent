"""
Browser/Application Agent (sections 5/20, Todo T3.2) — submits an APPROVED
application through the posting's application form via Playwright.

Hard guardrails (PRD §10 — enforced here, not just in the API layer):
1. The application must be in ApplicationStatus.approved. Anything else is
   refused — the human approval gate is absolute.
2. Never bypass CAPTCHA or anti-bot checks: detecting any captcha/anti-bot
   marker aborts immediately → needs_user_action.
3. Never invent answers: only the prepared answers_json Q&A, the prepared
   cover letter, and data already on the rows are used. Fields without a
   confident match are left untouched and reported.
4. Evidence: a best-effort screenshot per step under BROWSER_EVIDENCE_DIR/
   <application_id>/.

Status flow driven here:
    approved → submitting → applied            (BROWSER_AUTO_SUBMIT=true and
                                                the form accepted submission)
    approved → submitting → needs_user_action  (blocked, captcha, or the
                                                default BROWSER_AUTO_SUBMIT=
                                                false — the form is filled and
                                                evidenced; the human sends it)

Playwright is imported lazily: hosts without Playwright browsers can still
import this module (and the test suite) — submission fails with a clear
error at call time instead of at import time.
"""
import json
import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.application import Application, ApplicationStatus, StatusEvent
from app.models.job import Job
from app.services.notifications import notify

logger = logging.getLogger(__name__)

_CAPTCHA_MARKERS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cf-challenge",
    "are you a robot",
    "verify you are human",
)


def _evidence_dir(application_id: str):
    from pathlib import Path

    directory = Path(get_settings().BROWSER_EVIDENCE_DIR) / application_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _shot(page, application_id: str, name: str) -> str:
    """Best-effort screenshot — evidence must never break a submission run."""
    try:
        path = _evidence_dir(application_id) / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        return str(path)
    except Exception:
        logger.warning("screenshot %s failed; continuing without it", name)
        return ""


def _looks_like_captcha(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in _CAPTCHA_MARKERS)


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _best_answer(field_hint: str, answers: dict[str, str]) -> str | None:
    """Match a form field to a prepared answer by normalized substring overlap.
    Returns None when nothing matches confidently — we never guess."""
    hint = _norm(field_hint)
    if not hint:
        return None
    best_key = None
    best_score = 0
    for key, value in answers.items():
        candidate = _norm(key)
        if not candidate:
            continue
        if candidate == hint:
            score = 100
        elif candidate in hint or hint in candidate:
            score = max(len(candidate), len(hint))
        else:
            score = 0
        if score > best_score:
            best_score = score
            best_key = key
    # Refuse tiny/accidental overlaps: a wrong fill is worse than no fill.
    if best_key is None or best_score < 4:
        return None
    return answers[best_key]


def _field_hint(element) -> str:
    """Best human-readable hint for a field: label text, else aria-label /
    name / id / placeholder."""
    hint = element.get_attribute("aria-label") or ""
    element_id = element.get_attribute("id") or ""
    if element_id and not hint:
        try:
            label = element.page.locator(f"label[for='{element_id}']").first
            hint = (label.inner_text(timeout=1000) or "").strip()
        except Exception:
            pass
    hint = hint or element.get_attribute("name") or element_id
    return hint or element.get_attribute("placeholder") or ""


def _fill_page(page, answers: dict[str, str], cover_letter: str | None) -> list[str]:
    """Fill visible inputs/textareas with confident matches. Returns the hints
    of the fields actually filled (for the report)."""
    filled: list[str] = []
    fields = page.locator("input:visible, textarea:visible")
    count = fields.count()
    for index in range(min(count, 40)):  # safety cap
        element = fields.nth(index)
        try:
            field_type = (element.get_attribute("type") or "text").lower()
        except Exception:
            continue
        if field_type in {"hidden", "submit", "button", "checkbox", "radio", "file"}:
            continue
        hint = _field_hint(element)
        lowered = hint.lower()
        try:
            if field_type == "email" or "email" in lowered:
                if answers.get("email"):
                    element.fill(answers["email"])
                    filled.append("email")
                continue
            if "cover letter" in lowered or "cover_letter" in lowered:
                if cover_letter:
                    element.fill(cover_letter)
                    filled.append("cover letter")
                continue
            answer = _best_answer(hint, answers)
            if answer is None:
                continue
            tag = element.evaluate("el => el.tagName.toLowerCase()")
            if tag == "textarea" or field_type in {"text", "search", "tel", "url", ""}:
                element.fill(answer)
                filled.append(hint or f"field#{index}")
        except Exception:
            logger.debug("could not fill field %r; skipping", hint)
            continue
    return filled


def submit_application(db: Session, application: Application) -> dict:
    """Attempt browser submission of an APPROVED application. Returns a report
    dict (outcome, filled fields, screenshots); the application's status and
    timeline are updated to match the outcome. See module docstring."""
    settings = get_settings()

    # Guardrail 1: the approval gate, re-checked at the agent level.
    if application.status != ApplicationStatus.approved:
        raise ValueError(
            f"Application {application.id} is {application.status.value!r}; "
            "only 'approved' applications can be submitted"
        )

    job = db.get(Job, application.job_id)
    target_url = (job.application_url if job else None) or (job.url if job else None)
    if not target_url:
        raise ValueError(f"Application {application.id} has no application/job URL to submit to")

    # Guardrail 3: answers come only from the prepared application row.
    answers: dict[str, str] = {}
    if application.answers_json:
        try:
            loaded = json.loads(application.answers_json)
            if isinstance(loaded, dict):
                answers = {
                    str(key): str(value)
                    for key, value in loaded.items()
                    if str(value).strip()
                }
        except json.JSONDecodeError:
            logger.warning("answers_json for %s is not valid JSON; submitting without Q&A", application.id)

    def event(status: ApplicationStatus, note: str) -> None:
        db.add(StatusEvent(application_id=application.id, status=status, note=note))

    application.status = ApplicationStatus.submitting
    event(ApplicationStatus.submitting, f"browser agent started at {target_url}")
    db.commit()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        application.status = ApplicationStatus.needs_user_action
        event(ApplicationStatus.needs_user_action, "Playwright is not installed on this host")
        db.commit()
        raise ValueError("Playwright is not installed — run `playwright install` first") from exc

    report: dict = {
        "url": target_url,
        "filled": [],
        "screenshots": [],
        "auto_submit": settings.BROWSER_AUTO_SUBMIT,
    }
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=settings.BROWSER_HEADLESS)
            try:
                page = browser.new_context().new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=45_000)
                report["screenshots"].append(_shot(page, str(application.id), "01-landing"))

                # Guardrail 2: detect anti-bot challenges and stop immediately.
                if _looks_like_captcha(page.content()):
                    raise RuntimeError(
                        "CAPTCHA or anti-bot challenge detected — bypassing is not permitted"
                    )

                report["filled"] = _fill_page(page, answers, application.cover_letter)
                report["screenshots"].append(_shot(page, str(application.id), "02-filled"))

                if not settings.BROWSER_AUTO_SUBMIT:
                    application.status = ApplicationStatus.needs_user_action
                    event(
                        ApplicationStatus.needs_user_action,
                        f"form filled ({len(report['filled'])} fields) and evidenced — "
                        "review and send manually, or set BROWSER_AUTO_SUBMIT=true",
                    )
                    db.commit()
                    report["outcome"] = "needs_user_action"
                    return report

                # Explicitly enabled auto-submit: click the likeliest control.
                submit_control = page.locator(
                    "button[type='submit'], input[type='submit'], "
                    "button:has-text('submit'), button:has-text('apply')"
                ).first
                if submit_control.count() == 0:
                    raise RuntimeError("no submit control found on the page")
                submit_control.click(timeout=10_000)
                page.wait_for_load_state("domcontentloaded", timeout=30_000)
                report["screenshots"].append(_shot(page, str(application.id), "03-after-submit"))

                application.status = ApplicationStatus.applied
                event(ApplicationStatus.applied, "browser agent submitted the form")
                db.commit()
                report["outcome"] = "applied"
                return report
            finally:
                browser.close()
    except Exception as exc:
        logger.exception("browser submission failed for application %s", application.id)
        application.status = ApplicationStatus.needs_user_action
        event(ApplicationStatus.needs_user_action, f"browser agent blocked: {exc}")
        db.commit()
        report["outcome"] = "needs_user_action"
        report["error"] = str(exc)
        notify(
            "submission_blocked",
            f"Submission blocked for application {application.id}",
            str(exc),
        )
        return report
    finally:
        if report.get("outcome") in {"applied", "needs_user_action"}:
            notify(
                "submission_update",
                f"Application {application.id}: {report['outcome']}",
                f"filled {len(report.get('filled', []))} fields at {report.get('url', '')}",
            )