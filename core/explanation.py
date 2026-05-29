"""
Natural-language ranking explanations — LLM-powered (Groq) or rule-based fallback.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _resolve_api_key(api_key: str | None) -> str | None:
    """Return the API key provided by the UI, if any."""
    if api_key and api_key.strip():
        return api_key.strip()
    return None


def _fallback_explanation(candidate: dict[str, Any], scores: dict[str, Any]) -> str:
    """Generate a short heuristic explanation without an LLM."""
    reasons: list[str] = []
    if scores["semantic_score"] > 0.7:
        reasons.append("strong semantic alignment")
    elif scores["semantic_score"] > 0.5:
        reasons.append("moderate semantic alignment")
    if scores["momentum_score"] > 0.5:
        reasons.append("strong recent momentum")
    elif scores["momentum_score"] > 0.3:
        reasons.append("moderate recent momentum")

    explanation = f"**{candidate['name']}** is a strong fit because "
    if reasons:
        explanation += " and ".join(reasons) + "."
    else:
        explanation += "their overall profile is competitive."
    return explanation


def _is_auth_error(exc: Exception) -> bool:
    """Detect Groq/HF auth failures so we can fall back cleanly."""
    message = str(exc).lower()
    return (
        "401" in message
        or "invalid api key" in message
        or "invalid_request_error" in message
        or "authentication" in message
        or "unauthorized" in message
    )


def generate_explanation(
    candidate: dict[str, Any],
    job_description: str,
    scores: dict[str, Any],
    api_key: str | None = None,
) -> str:
    """
    Generate a human-readable explanation for why *candidate* ranks
    where they do against *job_description*.

    Uses the Groq LLM when an API key is available; otherwise falls back
    to a deterministic heuristic.
    """
    resolved_key = _resolve_api_key(api_key)

    if not resolved_key:
        return _fallback_explanation(candidate, scores)

    prompt = (
        f"Job: {job_description}\n"
        f"Candidate: {candidate['name']}\n"
        f"Semantic Match: {scores['semantic_score']}\n"
        f"Momentum Score: {scores['momentum_score']}\n\n"
        "Explain in one short sentence, max 25 words, why this candidate "
        "ranks highly based on these scores and their profile."
    )

    try:
        from groq import Groq  # type: ignore[import-untyped]

        client = Groq(api_key=resolved_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        if _is_auth_error(exc):
            logger.warning("Groq auth failed, using fallback explanation: %s", exc)
            return _fallback_explanation(candidate, scores)

        logger.error("LLM explanation failed: %s", exc)
        return _fallback_explanation(candidate, scores)
