"""Prompt templates for the Matching Agent's LLM reasoning step (section 11)."""

MATCH_SYSTEM_PROMPT = """You are an honest job-match evaluator for a candidate.
Return ONLY a single JSON object — no markdown, no commentary:
{"score": <int 0-100>, "category": "strong"|"possible"|"weak",
 "reasons": ["short, concrete reason", ...]}

Score how well the candidate fits the posting. Be conservative: 75+ only for
clear fits, 50-74 plausible fits, below 50 otherwise. NEVER invent candidate
facts — use only the profile provided. Always ground each reason in specifics
(matched skills, gaps, location/salary constraints)."""


def build_match_user_prompt(
    *,
    title: str | None,
    company: str | None,
    description: str | None,
    profile_text: str,
) -> str:
    return f"""# Job posting
Title: {title or "unknown"}
Company: {company or "unknown"}
Description:
{(description or "(unavailable)")[:6000]}

# Candidate profile
{profile_text or "(profile is empty)"}

Evaluate the fit now, as JSON."""
