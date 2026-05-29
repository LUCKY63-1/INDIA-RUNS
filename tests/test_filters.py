"""Tests for core.filters.filter_candidates."""
import pytest

from core.filters import filter_candidates


SAMPLE = [
    {
        "id": "1",
        "name": "Alice",
        "role": "Senior Software Engineer",
        "resume_text": "Python, React, AWS",
        "github_commits_last_90d": 120,
        "certifications_last_year": 2,
        "skills_acquired_last_180d": 3,
        "location": "San Francisco",
    },
    {
        "id": "2",
        "name": "Bob",
        "role": "Backend Developer",
        "resume_text": "Java, Spring Boot, PostgreSQL",
        "github_commits_last_90d": 10,
        "certifications_last_year": 0,
        "skills_acquired_last_180d": 0,
        "location": "New York",
    },
    {
        "id": "3",
        "name": "Charlie",
        "role": "Full Stack Engineer",
        "resume_text": "JavaScript, Next.js, React",
        "github_commits_last_90d": 250,
        "certifications_last_year": 5,
        "skills_acquired_last_180d": 6,
        "location": "Remote",
    },
]


class TestNoFilters:
    def test_returns_all(self):
        assert len(filter_candidates(SAMPLE)) == 3


class TestRoleFilter:
    def test_exact_role(self):
        result = filter_candidates(SAMPLE, role="Backend Developer")
        assert len(result) == 1
        assert result[0]["name"] == "Bob"

    def test_partial_role(self):
        result = filter_candidates(SAMPLE, role="engineer")
        assert len(result) == 2  # Senior Software Engineer + Full Stack Engineer

    def test_case_insensitive(self):
        result = filter_candidates(SAMPLE, role="BACKEND")
        assert len(result) == 1

    def test_no_match(self):
        result = filter_candidates(SAMPLE, role="Data Scientist")
        assert len(result) == 0


class TestSkillFilter:
    def test_single_skill(self):
        result = filter_candidates(SAMPLE, skill="python")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_shared_skill(self):
        result = filter_candidates(SAMPLE, skill="react")
        assert len(result) == 2  # Alice and Charlie


class TestNumericFilters:
    def test_min_commits(self):
        result = filter_candidates(SAMPLE, min_commits=100)
        assert len(result) == 2  # Alice (120) and Charlie (250)

    def test_min_certs(self):
        result = filter_candidates(SAMPLE, min_certs=3)
        assert len(result) == 1
        assert result[0]["name"] == "Charlie"

    def test_min_skills(self):
        result = filter_candidates(SAMPLE, min_skills=5)
        assert len(result) == 1


class TestLocationFilter:
    def test_location_match(self):
        result = filter_candidates(SAMPLE, location="San Francisco")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_location_no_match(self):
        result = filter_candidates(SAMPLE, location="London")
        assert len(result) == 0

    def test_missing_location_field(self):
        """Candidate without a location field should be excluded when filtering."""
        cands = [{"id": "x", "name": "X", "role": "Dev", "resume_text": "code"}]
        result = filter_candidates(cands, location="NYC")
        assert len(result) == 0


class TestCombinedFilters:
    def test_role_and_commits(self):
        result = filter_candidates(SAMPLE, role="engineer", min_commits=200)
        assert len(result) == 1
        assert result[0]["name"] == "Charlie"
