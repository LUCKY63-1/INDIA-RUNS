"""Tests for core.momentum.calculate_momentum_score."""
import pytest

from core.momentum import calculate_momentum_score


EVEN_WEIGHTS = {
    "github": 0.2,
    "linkedin": 0.2,
    "certs": 0.2,
    "growth": 0.2,
    "stability": 0.2,
}


def _candidate(**overrides):
    base = {
        "name": "Test",
        "github_commits_last_90d": 0,
        "linkedin_posts_last_30d": 0,
        "certifications_last_year": 0,
        "skills_acquired_last_180d": 0,
        "job_changes_last_2y": 0,
    }
    base.update(overrides)
    return base


class TestMomentumBasics:
    def test_all_zeros(self):
        """Zero activity → only stability contributes (0.5 * 0.2 = 0.1)."""
        score = calculate_momentum_score(_candidate(), EVEN_WEIGHTS)
        assert score == 0.1

    def test_max_everything(self):
        cand = _candidate(
            github_commits_last_90d=200,
            linkedin_posts_last_30d=30,
            certifications_last_year=10,
            skills_acquired_last_180d=15,
            job_changes_last_2y=1,
        )
        score = calculate_momentum_score(cand, EVEN_WEIGHTS)
        # All signals max out at 1.0, stability 1.0 for 1 change,
        # plus recency bonus for linkedin>10 and github>50
        assert score == 1.0  # clamped

    def test_score_is_clamped_to_1(self):
        """Even with extreme values, score must not exceed 1.0."""
        cand = _candidate(
            github_commits_last_90d=9999,
            linkedin_posts_last_30d=9999,
        )
        score = calculate_momentum_score(cand, EVEN_WEIGHTS)
        assert score <= 1.0


class TestStabilitySignal:
    def test_zero_changes(self):
        """0 job changes → stability_score = 0.5."""
        s = calculate_momentum_score(_candidate(job_changes_last_2y=0), EVEN_WEIGHTS)
        assert s == pytest.approx(0.1, abs=0.01)

    def test_one_change(self):
        """1 change → stability_score = 1.0."""
        s = calculate_momentum_score(_candidate(job_changes_last_2y=1), EVEN_WEIGHTS)
        assert s == pytest.approx(0.2, abs=0.01)

    def test_two_changes(self):
        """2 changes → stability_score = 1.0."""
        s = calculate_momentum_score(_candidate(job_changes_last_2y=2), EVEN_WEIGHTS)
        assert s == pytest.approx(0.2, abs=0.01)

    def test_three_changes_penalised(self):
        """3+ changes → stability_score = 0.3."""
        s = calculate_momentum_score(_candidate(job_changes_last_2y=5), EVEN_WEIGHTS)
        assert s == pytest.approx(0.06, abs=0.01)


class TestRecencyBonus:
    def test_no_bonus(self):
        """Low activity → no recency bonus applied."""
        cand = _candidate(linkedin_posts_last_30d=5, github_commits_last_90d=10)
        s = calculate_momentum_score(cand, EVEN_WEIGHTS)
        # github=0.1, linkedin=0.25, stability=0.5 → (0.1*0.2+0.25*0.2+0.5*0.2) = 0.17
        # no recency bonus
        assert s < 0.2

    def test_linkedin_bonus(self):
        """LinkedIn > 10 → +0.05 recency bonus."""
        base = _candidate(linkedin_posts_last_30d=5)
        bonus = _candidate(linkedin_posts_last_30d=15)
        s_base = calculate_momentum_score(base, EVEN_WEIGHTS)
        s_bonus = calculate_momentum_score(bonus, EVEN_WEIGHTS)
        assert s_bonus > s_base

    def test_github_bonus(self):
        """GitHub > 50 → +0.05 recency bonus."""
        base = _candidate(github_commits_last_90d=10)
        bonus = _candidate(github_commits_last_90d=60)
        s_base = calculate_momentum_score(base, EVEN_WEIGHTS)
        s_bonus = calculate_momentum_score(bonus, EVEN_WEIGHTS)
        assert s_bonus > s_base


class TestCustomWeights:
    def test_github_only(self):
        """Only github weight → only github signal matters."""
        weights = {"github": 1.0, "linkedin": 0.0, "certs": 0.0, "growth": 0.0, "stability": 0.0}
        cand = _candidate(github_commits_last_90d=50)
        s = calculate_momentum_score(cand, weights)
        assert s == pytest.approx(0.5, abs=0.05)

    def test_all_weights_zero(self):
        """All weights zero → score is 0."""
        weights = {"github": 0.0, "linkedin": 0.0, "certs": 0.0, "growth": 0.0, "stability": 0.0}
        s = calculate_momentum_score(_candidate(github_commits_last_90d=100), weights)
        assert s == 0.0
