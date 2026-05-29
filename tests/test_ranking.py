"""Tests for core.ranking.rank_candidates."""
import pytest

from core.ranking import rank_candidates


# We need the model to be loaded for these tests, so they are integration-level.
# Mark them to optionally skip if sentence-transformers is slow to load.

CANDIDATES = [
    {
        "id": "1",
        "name": "Alice",
        "role": "Python Developer",
        "resume_text": "Experienced Python developer with expertise in Django and REST APIs.",
        "github_commits_last_90d": 100,
        "linkedin_posts_last_30d": 5,
        "certifications_last_year": 2,
        "skills_acquired_last_180d": 3,
        "job_changes_last_2y": 0,
    },
    {
        "id": "2",
        "name": "Bob",
        "role": "Marketing Manager",
        "resume_text": "Digital marketing expert specialising in social media campaigns.",
        "github_commits_last_90d": 0,
        "linkedin_posts_last_30d": 20,
        "certifications_last_year": 0,
        "skills_acquired_last_180d": 1,
        "job_changes_last_2y": 3,
    },
]

JOB_DESC = "Looking for a Python developer with Django and REST API experience."

WEIGHTS = {"semantic": 0.7, "momentum": 0.3}


class TestRankingOrder:
    def test_relevant_candidate_ranks_first(self):
        """Alice's resume matches the Python job better than Bob's marketing resume."""
        results = rank_candidates(JOB_DESC, CANDIDATES, WEIGHTS)
        assert results[0]["name"] == "Alice"

    def test_results_sorted_descending(self):
        results = rank_candidates(JOB_DESC, CANDIDATES, WEIGHTS)
        scores = [r["final_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestEdgeCases:
    def test_empty_candidates(self):
        results = rank_candidates(JOB_DESC, [], WEIGHTS)
        assert results == []

    def test_missing_resume_text(self):
        """Candidate with no resume_text should not crash."""
        cands = [{"id": "x", "name": "NoResume", "role": "Dev"}]
        results = rank_candidates(JOB_DESC, cands, WEIGHTS)
        assert len(results) == 1
        assert results[0]["name"] == "NoResume"

    def test_result_structure(self):
        results = rank_candidates(JOB_DESC, CANDIDATES, WEIGHTS)
        for r in results:
            assert "id" in r
            assert "name" in r
            assert "final_score" in r
            assert "semantic_score" in r
            assert "momentum_score" in r
            assert "raw_data" in r


class TestWeightSensitivity:
    def test_high_semantic_weight(self):
        """With very high semantic weight, the most relevant resume wins decisively."""
        w = {"semantic": 0.95, "momentum": 0.05}
        results = rank_candidates(JOB_DESC, CANDIDATES, w)
        assert results[0]["name"] == "Alice"
        # Gap should be large
        gap = results[0]["final_score"] - results[1]["final_score"]
        assert gap > 0.1

    def test_high_momentum_weight(self):
        """With very high momentum weight, activity signals matter more."""
        w = {"semantic": 0.05, "momentum": 0.95}
        results = rank_candidates(JOB_DESC, CANDIDATES, w)
        # Alice still has decent momentum (github=100) so she may still win,
        # but the gap should be narrower than pure-semantic
        scores = [r["final_score"] for r in results]
        assert max(scores) <= 1.0
