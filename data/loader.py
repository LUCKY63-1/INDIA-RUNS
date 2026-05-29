"""
Data loading utilities — JSON, CSV, PDF, and DOCX parsing with validation.
"""
from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON / CSV helpers
# ---------------------------------------------------------------------------
def load_json(path: str) -> list[dict[str, Any]] | dict[str, Any]:
    """Load and parse a JSON file with error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded JSON from %s", path)
        return data
    except FileNotFoundError:
        logger.error("File not found: %s", path)
        return []
    except json.JSONDecodeError as exc:
        logger.error("Malformed JSON in %s: %s", path, exc)
        return []


def save_json(path: str, data: Any) -> bool:
    """Write data to a JSON file. Returns True on success."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info("Saved JSON to %s", path)
        return True
    except Exception as exc:
        logger.error("Failed to save JSON to %s: %s", path, exc)
        return False


def load_uploaded_json(file_obj: Any) -> list[dict[str, Any]]:
    """Parse an uploaded JSON file object (Streamlit UploadedFile)."""
    try:
        data = json.load(file_obj)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            logger.warning("Uploaded JSON is a dict; wrapping in list.")
            return [data]
        logger.warning(
            "Uploaded JSON is type %s; expected list or dict. Returning empty list.",
            type(data).__name__,
        )
        return []
    except json.JSONDecodeError as exc:
        logger.error("Malformed JSON upload: %s", exc)
        return []


def load_uploaded_csv(file_obj: Any) -> list[dict[str, Any]]:
    """Parse an uploaded CSV file object into a list of dicts."""
    try:
        import pandas as pd  # type: ignore[import-untyped]

        df = pd.read_csv(file_obj)
        return df.to_dict(orient="records")
    except ImportError:
        logger.error("pandas not installed – cannot parse CSV.")
        return []
    except Exception as exc:
        logger.error("Failed to parse CSV upload: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Document parsing (PDF / DOCX)
# ---------------------------------------------------------------------------
def parse_pdf(file_obj: Any) -> str:
    """Extract plain text from a PDF file-like object."""
    try:
        import pdfplumber  # type: ignore[import-untyped]
    except ImportError:
        logger.error("pdfplumber not installed – cannot parse PDF. Install with: pip install pdfplumber")
        return ""

    try:
        text_parts: list[str] = []
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        result = "\n".join(text_parts)
        logger.info("Extracted %d chars from PDF.", len(result))
        return result
    except Exception as exc:
        logger.error("PDF parsing failed: %s", exc)
        return ""


def parse_docx(file_obj: Any) -> str:
    """Extract plain text from a DOCX file-like object."""
    try:
        import docx  # type: ignore[import-untyped]
    except ImportError:
        logger.error("python-docx not installed – cannot parse DOCX. Install with: pip install python-docx")
        return ""

    try:
        doc = docx.Document(file_obj)
        result = "\n".join(para.text for para in doc.paragraphs if para.text)
        logger.info("Extracted %d chars from DOCX.", len(result))
        return result
    except Exception as exc:
        logger.error("DOCX parsing failed: %s", exc)
        return ""


def load_uploaded_file(file_obj: Any) -> list[dict[str, Any]] | str:
    """
    Unified upload handler.

    - JSON / CSV  → returns list[dict]
    - PDF / DOCX  → returns extracted text (str)
    """
    name: str = getattr(file_obj, "name", "")
    lower = name.lower()

    if lower.endswith(".json"):
        return load_uploaded_json(file_obj)
    if lower.endswith(".csv"):
        return load_uploaded_csv(file_obj)
    if lower.endswith(".pdf"):
        return parse_pdf(file_obj)
    if lower.endswith(".docx"):
        return parse_docx(file_obj)

    logger.warning("Unsupported file type: %s (.json, .csv, .pdf, .docx supported)", name)
    return []
