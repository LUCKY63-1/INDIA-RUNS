"""
Candidate filtering logic extracted from the UI layer.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def filter_candidates(
    candidates: list[dict[str, Any]],
    *,
    role: str = "",
    skill: str = "",
    min_commits: int = 0,
    min_certs: int = 0,
    min_skills: int = 0,
    location: str = "",
) -> list[dict[str, Any]]:
    """
    Return only candidates matching **all** supplied filter criteria.

    All text filters are case-insensitive substring matches.
    Numeric filters are lower-bound inclusive thresholds.
    """
    filtered: list[dict[str, Any]] = []

    for cand in candidates:
        if role and role.lower() not in cand.get("role", "").lower():
            continue
        if skill and skill.lower() not in cand.get("resume_text", "").lower():
            continue
        if cand.get("github_commits_last_90d", 0) < min_commits:
            continue
        if cand.get("certifications_last_year", 0) < min_certs:
            continue
        if cand.get("skills_acquired_last_180d", 0) < min_skills:
            continue
        if location and location.lower() not in cand.get("location", "").lower():
            continue
        filtered.append(cand)

    logger.info(
        "Filtered %d → %d candidates (role=%r, skill=%r)",
        len(candidates),
        len(filtered),
        role,
        skill,
    )
    return filtered
