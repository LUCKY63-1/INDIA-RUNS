"""
Resume ingestion helpers for PDF uploads.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Any

from core.skills import extract_skills
from data.loader import load_json, parse_pdf, save_json

logger = logging.getLogger(__name__)

MOMENTUM_FIELD_DEFAULTS: dict[str, int] = {
    "github_commits_last_90d": 0,
    "job_changes_last_2y": 0,
    "certifications_last_year": 0,
    "linkedin_posts_last_30d": 0,
    "skills_acquired_last_180d": 0,
}


def build_resume_prompt(resume_text: str) -> str:
    """Build a strict prompt that instructs TinyLM to emit JSON only."""
    schema = {
        "id": "string",
        "name": "string",
        "role": "string",
        "location": "string or null",
        "summary": "string or null",
        "resume_text": "string",
        "skills": ["string"],
        "github_commits_last_90d": 0,
        "job_changes_last_2y": 0,
        "certifications_last_year": 0,
        "linkedin_posts_last_30d": 0,
        "skills_acquired_last_180d": 0,
    }

    return (
        "You are a resume parser. Return only one valid JSON object.\n"
        "Do not wrap the JSON in markdown fences. Do not add prose.\n"
        "Use null for unknown strings, an empty list for unknown skills, and 0 for unknown numeric signals.\n"
        "Fill the exact keys shown in the schema. If a field is not present in the resume, infer it conservatively.\n"
        f"Schema: {json.dumps(schema, ensure_ascii=False)}\n\n"
        "Resume text:\n"
        "<<<RESUME_START>>>\n"
        f"{resume_text.strip()}\n"
        "<<<RESUME_END>>>"
    )


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json_fragment(text: str) -> str | None:
    cleaned = _strip_code_fences(text)
    if not cleaned:
        return None

    candidates = [cleaned]
    if "{" in cleaned and "}" in cleaned:
        candidates.append(cleaned[cleaned.find("{") : cleaned.rfind("}") + 1])
    if "[" in cleaned and "]" in cleaned:
        candidates.append(cleaned[cleaned.find("[") : cleaned.rfind("]") + 1])

    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
        try:
            decoded, _ = decoder.raw_decode(candidate)
            return json.dumps(decoded)
        except json.JSONDecodeError:
            continue
    return None


def parse_structured_resume_output(text: str) -> dict[str, Any] | None:
    """Parse TinyLM output and return the first JSON object, if present."""
    fragment = _extract_json_fragment(text)
    if not fragment:
        return None

    try:
        payload = json.loads(fragment)
    except json.JSONDecodeError:
        logger.warning("Resume LLM output could not be parsed as JSON.")
        return None

    if isinstance(payload, list):
        payload = next((item for item in payload if isinstance(item, dict)), None)

    return payload if isinstance(payload, dict) else None


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _guess_role(resume_text: str, skills: list[str]) -> str:
    if skills:
        if any(skill in {"seo", "content marketing", "social media", "google analytics"} for skill in skills):
            return "Marketing Specialist"
        if any(
            skill in {"python", "java", "javascript", "typescript", "react", "node.js", "aws", "docker", "kubernetes"}
            for skill in skills
        ):
            return "Software Engineer"
        if any(skill in {"data science", "machine learning", "pandas", "numpy", "tensorflow", "pytorch", "llm", "llms"} for skill in skills):
            return "Data Scientist"

    for line in resume_text.splitlines():
        candidate_line = line.strip()
        if 4 <= len(candidate_line) <= 80:
            return candidate_line
    return "Imported Candidate"


def _build_candidate_id(name: str, source_name: str, resume_text: str) -> str:
    base = f"{name}|{source_name}|{resume_text}".encode("utf-8", errors="ignore")
    digest = hashlib.sha1(base).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "candidate"
    return f"resume_{slug}_{digest}"


def _fallback_candidate(resume_text: str, source_name: str) -> dict[str, Any]:
    skills = sorted(extract_skills(resume_text))
    role = _guess_role(resume_text, skills)
    name = os.path.splitext(os.path.basename(source_name or ""))[0].strip() or "Imported Candidate"
    return {
        "name": name,
        "role": role,
        "location": None,
        "summary": None,
        "resume_text": resume_text.strip(),
        "skills": skills,
        "github_commits_last_90d": 0,
        "job_changes_last_2y": 0,
        "certifications_last_year": 0,
        "linkedin_posts_last_30d": 0,
        "skills_acquired_last_180d": min(len(skills), 10),
    }


def _call_local_tinylm(prompt: str, model_name: str) -> str:
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
        },
    }
    request = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read().decode("utf-8")

    parsed = json.loads(body)
    if isinstance(parsed, dict):
        return _clean_text(parsed.get("response"))
    return _clean_text(body)


def build_candidate_from_resume_text(
    resume_text: str,
    source_name: str = "",
    model_name: str | None = None,
) -> dict[str, Any]:
    """Create a normalized candidate record from raw resume text."""
    prompt = build_resume_prompt(resume_text)
    resolved_model = (model_name or os.getenv("RESUME_EXTRACTION_MODEL") or "tinyllama").strip()

    parsed: dict[str, Any] | None = None
    try:
        raw_output = _call_local_tinylm(prompt, resolved_model)
        parsed = parse_structured_resume_output(raw_output)
        if not parsed:
            logger.warning("TinyLM returned no usable JSON; using fallback candidate builder.")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning("TinyLM resume extraction failed, using fallback: %s", exc)

    candidate = dict(parsed or _fallback_candidate(resume_text, source_name))
    candidate["resume_text"] = _clean_text(candidate.get("resume_text")) or resume_text.strip()

    skills = candidate.get("skills")
    if not isinstance(skills, list):
        skills = []
    normalized_skills = sorted({str(skill).strip() for skill in skills if str(skill).strip()})
    if not normalized_skills:
        normalized_skills = sorted(extract_skills(candidate["resume_text"]))
    candidate["skills"] = normalized_skills

    candidate["name"] = _clean_text(candidate.get("name")) or _fallback_candidate(resume_text, source_name)["name"]
    candidate["role"] = _clean_text(candidate.get("role")) or _guess_role(candidate["resume_text"], candidate["skills"])
    candidate["location"] = candidate.get("location") if candidate.get("location") not in ("", None) else None
    candidate["summary"] = _clean_text(candidate.get("summary")) or None

    for field_name, default_value in MOMENTUM_FIELD_DEFAULTS.items():
        if field_name == "skills_acquired_last_180d":
            inferred_default = min(len(candidate["skills"]), 10)
            candidate[field_name] = _coerce_int(candidate.get(field_name), inferred_default)
            if candidate[field_name] == 0 and inferred_default:
                candidate[field_name] = inferred_default
        else:
            candidate[field_name] = _coerce_int(candidate.get(field_name), default_value)

    candidate["id"] = _clean_text(candidate.get("id")) or _build_candidate_id(
        candidate["name"],
        source_name,
        candidate["resume_text"],
    )
    candidate["source_file"] = source_name or candidate.get("source_file") or ""
    candidate["source"] = _clean_text(candidate.get("source")) or "pdf_resume_upload"
    return candidate


def ingest_pdf_resume_to_candidate(
    file_obj: Any,
    model_name: str | None = None,
) -> dict[str, Any] | None:
    """Extract text from a PDF upload and convert it into a candidate."""
    resume_text = parse_pdf(file_obj)
    if not resume_text.strip():
        return None
    return build_candidate_from_resume_text(resume_text, getattr(file_obj, "name", ""), model_name=model_name)


def append_candidate_to_json_dataset(path: str, candidate: dict[str, Any]) -> bool:
    """Append a normalized candidate to a JSON list file."""
    dataset = load_json(path)
    if not isinstance(dataset, list):
        dataset = []
    dataset.append(candidate)
    return save_json(path, dataset)