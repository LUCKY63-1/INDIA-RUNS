"""Tests for core.explanation (fallback path only — no LLM calls)."""
import pytest

from core.explanation import generate_explanation, _fallback_explanation


def _make_scores(semantic: float, momentum: float):
    return {
        "name": "Test User",
        "semantic_score": semantic,
        "momentum_score": momentum,
    }


class TestFallbackExplanation:
    def test_high_semantic_and_momentum(self):
        scores = _make_scores(0.8, 0.6)
        result = _fallback_explanation(scores, scores)
        assert "strong semantic alignment" in result
        assert "strong recent momentum" in result

    def test_moderate_scores(self):
        scores = _make_scores(0.55, 0.35)
        result = _fallback_explanation(scores, scores)
        assert "moderate" in result

    def test_low_scores(self):
        scores = _make_scores(0.2, 0.1)
        result = _fallback_explanation(scores, scores)
        assert "competitive" in result  # generic fallback

    def test_contains_candidate_name(self):
        scores = _make_scores(0.9, 0.9)
        result = _fallback_explanation(scores, scores)
        assert "Test User" in result


class TestGenerateExplanation:
    def test_no_api_key_uses_fallback(self):
        scores = _make_scores(0.8, 0.6)
        result = generate_explanation(scores, "Some job desc", scores, api_key=None)
        assert "strong semantic alignment" in result

    def test_empty_api_key_uses_fallback(self):
        scores = _make_scores(0.8, 0.6)
        result = generate_explanation(scores, "Some job desc", scores, api_key="")
        assert "strong semantic alignment" in result

    def test_whitespace_api_key_uses_fallback(self):
        scores = _make_scores(0.8, 0.6)
        result = generate_explanation(scores, "Some job desc", scores, api_key="   ")
        assert "Test User" in result
