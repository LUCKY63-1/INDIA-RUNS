"""
Dataset profiling and job suggestion logic.

Shared across Streamlit, Flet, and desktop apps to keep
``infer_dataset_profile()`` and ``suggest_job_titles()`` in one place.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Keyword lists used to guess the domain of a candidate dataset.
_MARKETING_KEYWORDS = [
    "seo", "social media", "content", "marketing", "campaign",
    "brand", "google analytics", "organic", "copywriting", "b2b",
]
_TECH_KEYWORDS = [
    "java", "spring", "backend", "full stack", "react", "node",
    "aws", "devops", "cloud", "python", "data scientist", "terraform",
]

_PROFILE_KEYWORDS: dict[str, list[str]] = {
    "marketing": ["seo", "marketing", "social", "content", "analytics", "brand", "campaign"],
    "tech": [
        "java", "spring", "backend", "full stack", "react", "node",
        "aws", "devops", "cloud", "python",
    ],
    "mixed": ["developer", "engineer", "marketing", "content"],
}


def infer_dataset_profile(
    candidates: list[dict[str, Any]],
    dataset_path: str = "",
) -> str:
    """Guess whether the loaded candidates are *marketing*, *tech*, or *mixed*.

    The function lowercases *dataset_path* and scans every candidate's
    ``role`` and ``resume_text`` for marketing/tech keyword hits.
    """
    text_bits = [dataset_path.lower()]
    for cand in candidates:
        text_bits.append(str(cand.get("role", "")).lower())
        text_bits.append(str(cand.get("resume_text", "")).lower())

    text = " ".join(text_bits)
    marketing_score = sum(text.count(term) for term in _MARKETING_KEYWORDS)
    tech_score = sum(text.count(term) for term in _TECH_KEYWORDS)

    if marketing_score > tech_score:
        return "marketing"
    if tech_score > marketing_score:
        return "tech"
    return "mixed"


def suggest_job_titles(
    profile: str,
    jobs_data: list[dict[str, Any]],
) -> list[str]:
    """Return the most relevant job titles for the given *profile*.

    Scores each job by keyword overlap with the profile's keyword list.
    Falls back to the first job if nothing scores.
    """
    if not jobs_data:
        return []

    keywords = _PROFILE_KEYWORDS.get(profile, _PROFILE_KEYWORDS["mixed"])

    scored: list[tuple[int, str]] = []
    for job in jobs_data:
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        score = sum(job_text.count(kw) for kw in keywords)
        scored.append((score, str(job.get("title", ""))))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    top = [title for score, title in scored if score > 0][:2]
    if top:
        return top

    if profile == "marketing":
        marketing_titles = [
            str(job.get("title", ""))
            for job in jobs_data
            if any(k in str(job.get("title", "")).lower()
                   for k in ["seo", "social", "content", "marketing"])
        ]
        if marketing_titles:
            return marketing_titles[:2]

    return [str(jobs_data[0].get("title", ""))]