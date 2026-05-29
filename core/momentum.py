"""
Behavioural momentum scoring from candidate activity signals.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def calculate_momentum_score(
    candidate: dict[str, Any],
    m_weights: dict[str, float],
) -> float:
    """
    Calculate a composite momentum score from configurable behavioural signals.

    Parameters
    ----------
    candidate : dict
        Candidate record with activity fields.
    m_weights : dict
        Per-signal weights (github, linkedin, certs, growth, stability).

    Returns
    -------
    float
        Momentum score clamped to [0, 1].
    """
    # 1. GitHub Activity (normalised to 100 commits)
    github_score = min(candidate.get("github_commits_last_90d", 0) / 100, 1.0)

    # 2. LinkedIn Activity (normalised to 20 posts)
    linkedin_score = min(candidate.get("linkedin_posts_last_30d", 0) / 20, 1.0)

    # 3. Certifications (normalised to 5 certs)
    cert_score = min(candidate.get("certifications_last_year", 0) / 5, 1.0)

    # 4. Growth Velocity (normalised to 10 skills)
    growth_score = min(candidate.get("skills_acquired_last_180d", 0) / 10, 1.0)

    # 5. Stability / Job-Change Signal
    #    1-2 changes → active (1.0), 0 → stable (0.5), >2 → job-hopping (0.3)
    changes = candidate.get("job_changes_last_2y", 0)
    if 1 <= changes <= 2:
        stability_score = 1.0
    elif changes == 0:
        stability_score = 0.5
    else:
        stability_score = 0.3

    score = (
        github_score * m_weights.get("github", 0.2)
        + linkedin_score * m_weights.get("linkedin", 0.2)
        + cert_score * m_weights.get("certs", 0.2)
        + growth_score * m_weights.get("growth", 0.2)
        + stability_score * m_weights.get("stability", 0.2)
    )

    # Recency bonus for very active candidates
    recency_bonus = 1.0
    if candidate.get("linkedin_posts_last_30d", 0) > 10:
        recency_bonus += 0.05
    if candidate.get("github_commits_last_90d", 0) > 50:
        recency_bonus += 0.05

    final = round(min(score * recency_bonus, 1.0), 2)
    logger.debug(
        "Momentum for %s: %.2f (bonus=%.2f)",
        candidate.get("name", "?"),
        final,
        recency_bonus,
    )
    return final
