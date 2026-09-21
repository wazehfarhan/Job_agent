"""
Notifications (section 19, Todo T3.3) — fire-and-forget; a notification
failure must never break the caller (matching, transitions, submissions).

Channels, all optional via env:
- NOTIFY_WEBHOOK_URL → POST {"event", "subject", "body"} as JSON
- NOTIFY_SMTP_*      → plain-text email to NOTIFY_EMAIL_TO

Nothing configured → the notification is logged (still visible in app/worker
logs), never silently dropped at the call site.
"""
import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _send_webhook(url: str, event: str, subject: str, body: str) -> None:
    httpx.post(url, json={"event": event, "subject": subject, "body": body}, timeout=10)


def _send_email(settings, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.NOTIFY_EMAIL_FROM or "job-agent@localhost"
    message["To"] = settings.NOTIFY_EMAIL_TO or ""
    message["Subject"] = subject
    message.set_content(body or subject)
    with smtplib.SMTP(settings.NOTIFY_SMTP_HOST, settings.NOTIFY_SMTP_PORT, timeout=15) as server:
        if settings.NOTIFY_SMTP_PORT == 587:
            server.starttls()
        if settings.NOTIFY_SMTP_USER and settings.NOTIFY_SMTP_PASSWORD:
            server.login(settings.NOTIFY_SMTP_USER, settings.NOTIFY_SMTP_PASSWORD)
        server.send_message(message)


def notify(event: str, subject: str, body: str = "") -> None:
    """Send a notification through every configured channel. Never raises."""
    settings = get_settings()
    delivered: list[str] = []

    if settings.NOTIFY_WEBHOOK_URL:
        try:
            _send_webhook(settings.NOTIFY_WEBHOOK_URL, event, subject, body)
            delivered.append("webhook")
        except Exception:
            logger.exception("webhook notification failed (event=%s)", event)

    if settings.NOTIFY_SMTP_HOST and settings.NOTIFY_EMAIL_TO:
        try:
            _send_email(settings, subject, body)
            delivered.append("email")
        except Exception:
            logger.exception("email notification failed (event=%s)", event)

    if delivered:
        logger.info("notification sent via %s: [%s] %s", "+".join(delivered), event, subject)
    else:
        logger.info("notification (no channels configured): [%s] %s", event, subject)