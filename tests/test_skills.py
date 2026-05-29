"""Tests for core.skills — extraction and gap analysis."""
import pytest

from core.skills import extract_skills, analyse_skill_gap, TECH_SKILLS, MARKETING_SKILLS


class TestExtractSkills:
    def test_single_skill(self):
        assert "python" in extract_skills("Experienced Python developer")

    def test_multiple_skills(self):
        found = extract_skills("Expert in React, Node.js, and AWS deployments")
        assert "react" in found
        assert "node.js" in found
        assert "aws" in found

    def test_case_insensitive(self):
        found = extract_skills("Skilled in KUBERNETES and Docker")
        assert "kubernetes" in found
        assert "docker" in found

    def test_no_skills(self):
        found = extract_skills("Enjoys long walks on the beach")
        assert len(found) == 0

    def test_marketing_skills(self):
        found = extract_skills("SEO specialist with Google Analytics expertise")
        assert "seo" in found
        assert "google analytics" in found

    def test_custom_skill_set(self):
        custom = {"python", "java"}
        found = extract_skills("Python and Rust developer", skill_set=custom)
        assert "python" in found
        assert "rust" not in found  # not in custom set

    def test_multi_word_skill(self):
        found = extract_skills("Using machine learning for NLP tasks")
        assert "machine learning" in found
        assert "nlp" in found


class TestAnalyseSkillGap:
    def test_full_overlap(self):
        cand = {"resume_text": "Expert in Python, React, and AWS"}
        job = "We need Python, React, and AWS skills"
        gap = analyse_skill_gap(cand, job)
        assert gap.overlap_pct == 100.0
        assert len(gap.missing) == 0

    def test_partial_overlap(self):
        cand = {"resume_text": "Python developer"}
        job = "Need Python and React expertise"
        gap = analyse_skill_gap(cand, job)
        assert "python" in gap.matched
        assert "react" in gap.missing
        assert gap.overlap_pct == 50.0

    def test_no_overlap(self):
        cand = {"resume_text": "Java and Spring Boot specialist"}
        job = "Looking for Python and React developer"
        gap = analyse_skill_gap(cand, job)
        assert gap.overlap_pct == 0.0
        assert len(gap.matched) == 0

    def test_extra_skills(self):
        cand = {"resume_text": "Python, React, Docker, Kubernetes expert"}
        job = "Need Python developer"
        gap = analyse_skill_gap(cand, job)
        assert "python" in gap.matched
        assert len(gap.extra) > 0

    def test_empty_resume(self):
        cand = {"resume_text": ""}
        job = "Need Python developer"
        gap = analyse_skill_gap(cand, job)
        assert gap.overlap_pct == 0.0

    def test_empty_job(self):
        cand = {"resume_text": "Python developer"}
        job = "Great team environment, competitive salary"
        gap = analyse_skill_gap(cand, job)
        # No skills in job → 100% overlap (vacuously)
        assert gap.overlap_pct == 100.0
