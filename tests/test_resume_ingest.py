"""Tests for data.resume_ingest."""
from __future__ import annotations

from unittest.mock import patch

from data.resume_ingest import (
    build_candidate_from_resume_text,
    build_resume_prompt,
    parse_structured_resume_output,
)


class TestResumePrompt:
    def test_prompt_is_strict_json_only(self):
        prompt = build_resume_prompt("Python developer with AWS experience")
        assert "Return only one valid JSON object" in prompt
        assert "Do not wrap the JSON in markdown fences" in prompt
        assert "<<<RESUME_START>>>" in prompt
        assert "Python developer with AWS experience" in prompt


class TestResumeJsonParsing:
    def test_parse_structured_resume_output_handles_code_fences(self):
        raw = "```json\n{\"name\": \"Avery Chen\", \"role\": \"Engineer\"}\n```"
        parsed = parse_structured_resume_output(raw)
        assert parsed is not None
        assert parsed["name"] == "Avery Chen"
        assert parsed["role"] == "Engineer"

    def test_parse_structured_resume_output_handles_json_array(self):
        raw = "[{\"name\": \"Avery Chen\", \"role\": \"Engineer\"}]"
        parsed = parse_structured_resume_output(raw)
        assert parsed is not None
        assert parsed["name"] == "Avery Chen"


class TestResumeFallbackNormalization:
    def test_fallback_builds_complete_candidate(self):
        with patch("data.resume_ingest._call_local_tinylm", side_effect=OSError("offline")):
            candidate = build_candidate_from_resume_text(
                "Python, React, and AWS engineer with product experience.",
                "avery_chen_resume.pdf",
            )

        assert candidate["name"] == "avery_chen_resume"
        assert candidate["resume_text"] == "Python, React, and AWS engineer with product experience."
        assert candidate["github_commits_last_90d"] == 0
        assert candidate["job_changes_last_2y"] == 0
        assert candidate["certifications_last_year"] == 0
        assert candidate["linkedin_posts_last_30d"] == 0
        assert candidate["skills_acquired_last_180d"] >= 3
        assert "python" in candidate["skills"]