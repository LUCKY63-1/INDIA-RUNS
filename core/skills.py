"""
Skill extraction and gap analysis.

Uses a curated keyword dictionary to identify skills in free-text resumes and
compare them against job description requirements.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated skill dictionaries (lowercase)
# ---------------------------------------------------------------------------
TECH_SKILLS: set[str] = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "sql", "html", "css",
    # Frameworks & Libraries
    "react", "angular", "vue", "vue.js", "next.js", "node.js", "express",
    "django", "flask", "fastapi", "spring boot", "spring", ".net", "rails",
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy",
    "streamlit", "svelte",
    # Cloud & Infra
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "ci/cd", "github actions", "gitlab ci",
    # Data
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "kafka",
    "spark", "airflow", "snowflake", "bigquery", "dbt",
    # ML / AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "llm", "llms", "generative ai", "rag",
    "reinforcement learning", "transformers",
    # Other
    "microservices", "rest api", "graphql", "agile", "scrum", "git",
    "linux", "devops", "data engineering", "data science",
}

MARKETING_SKILLS: set[str] = {
    "seo", "sem", "google analytics", "google ads", "facebook ads",
    "content marketing", "social media", "email marketing", "copywriting",
    "brand strategy", "marketing automation", "hubspot", "salesforce",
    "a/b testing", "conversion optimization", "ppc", "crm",
    "influencer marketing", "pr", "public relations", "market research",
}

ALL_SKILLS: set[str] = TECH_SKILLS | MARKETING_SKILLS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalise(text: str) -> str:
    """Lowercase and collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower().strip())


def extract_skills(text: str, skill_set: set[str] | None = None) -> set[str]:
    """
    Extract known skills from *text* by whole-word matching against
    the curated dictionary.
    """
    if skill_set is None:
        skill_set = ALL_SKILLS

    normalised = _normalise(text)
    found: set[str] = set()
    for skill in skill_set:
        # Use regex word boundaries for accurate matching
        # Escape the skill string as it might contain regex characters like '+'
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalised):
            found.add(skill)
    return found


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------
@dataclass
class SkillGap:
    """Result of comparing candidate skills to job requirements."""

    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    overlap_pct: float = 0.0


def analyse_skill_gap(
    candidate: dict[str, Any],
    job_description: str,
) -> SkillGap:
    """
    Compare skills extracted from a candidate's resume against those
    extracted from the job description.
    """
    cand_skills = extract_skills(candidate.get("resume_text", ""))
    job_skills = extract_skills(job_description)

    if not job_skills:
        logger.debug("No skills extracted from job description.")
        return SkillGap(
            matched=sorted(cand_skills),
            missing=[],
            extra=sorted(cand_skills),
            overlap_pct=100.0 if cand_skills else 0.0,
        )

    matched = sorted(cand_skills & job_skills)
    missing = sorted(job_skills - cand_skills)
    extra = sorted(cand_skills - job_skills)
    overlap_pct = round(len(matched) / len(job_skills) * 100, 1)

    logger.debug(
        "Skill gap for %s: %d matched, %d missing, %.1f%% overlap",
        candidate.get("name", "?"),
        len(matched),
        len(missing),
        overlap_pct,
    )

    return SkillGap(
        matched=matched,
        missing=missing,
        extra=extra,
        overlap_pct=overlap_pct,
    )
