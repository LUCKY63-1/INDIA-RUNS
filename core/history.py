"""
Ranking history — save / load ranking snapshots for audit trail and comparison.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# History directory lives alongside the data/ folder
_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
HISTORY_DIR = os.path.join(_BASE_DIR, "data", "history")


def _ensure_history_dir() -> None:
    os.makedirs(HISTORY_DIR, exist_ok=True)


def save_snapshot(
    job_title: str,
    results: list[dict[str, Any]],
    weights: dict[str, float],
    momentum_config: dict[str, float],
) -> str:
    """
    Persist a ranking run as a timestamped JSON snapshot.

    Returns the filename of the saved snapshot.
    """
    _ensure_history_dir()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"ranking_{ts}.json"
    filepath = os.path.join(HISTORY_DIR, filename)

    # Strip raw_data to keep snapshots lean
    slim_results = []
    for r in results:
        slim = {k: v for k, v in r.items() if k != "raw_data"}
        slim_results.append(slim)

    snapshot = {
        "timestamp": ts,
        "job_title": job_title,
        "weights": weights,
        "momentum_config": momentum_config,
        "candidate_count": len(slim_results),
        "results": slim_results,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        logger.info("Saved ranking snapshot → %s", filename)
    except OSError as exc:
        logger.error("Failed to save snapshot to %s: %s", filepath, exc)
        raise

    return filename


def list_snapshots() -> list[str]:
    """Return filenames of all saved snapshots, newest first."""
    _ensure_history_dir()
    try:
        files = [
            f
            for f in os.listdir(HISTORY_DIR)
            if f.startswith("ranking_") and f.endswith(".json")
        ]
    except OSError as exc:
        logger.error("Error listing snapshots in %s: %s", HISTORY_DIR, exc)
        return []
    return sorted(files, reverse=True)


def load_snapshot(filename: str) -> dict[str, Any]:
    """Load a snapshot by filename."""
    if not filename:
        logger.warning("load_snapshot called with empty filename.")
        return {}

    filepath = os.path.join(HISTORY_DIR, filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error("Snapshot file not found: %s", filepath)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Malformed snapshot JSON in %s: %s", filepath, exc)
        return {}
    except OSError as exc:
        logger.error("Error reading snapshot %s: %s", filepath, exc)
        return {}

    if not isinstance(data, dict):
        logger.error("Snapshot %s does not contain a JSON object.", filepath)
        return {}

    return data
