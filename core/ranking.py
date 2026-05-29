"""
Multi-factor candidate ranking with batched embedding computation.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from core.momentum import calculate_momentum_score
from utils.embeddings import get_model

logger = logging.getLogger(__name__)


def rank_candidates(
    job_description: str,
    candidates: list[dict[str, Any]],
    weights: dict[str, float],
    momentum_config: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """
    Rank *candidates* against a *job_description* using a weighted blend of
    semantic similarity and behavioural momentum.

    Embeddings are computed in a single batched call for performance.
    """
    if not candidates:
        logger.warning("rank_candidates called with an empty candidate list.")
        return []

    if momentum_config is None:
        momentum_config = {
            "github": 0.2,
            "linkedin": 0.2,
            "certs": 0.2,
            "growth": 0.2,
            "stability": 0.2,
        }

    model = get_model()

    # --- Batched encoding (5-10× faster than per-candidate calls) ----------
    logger.info("Encoding job description …")
    job_emb = model.encode([job_description])

    resume_texts: list[str] = []
    for cand in candidates:
        text = cand.get("resume_text", "")
        if not text:
            logger.warning(
                "Candidate %s (%s) has no resume_text – using empty string.",
                cand.get("id", "?"),
                cand.get("name", "?"),
            )
        resume_texts.append(text or "")

    logger.info("Batch-encoding %d candidate resumes …", len(resume_texts))
    all_resume_embs = model.encode(resume_texts)
    all_semantic_scores = cosine_similarity(job_emb, all_resume_embs)[0]

    # --- Score each candidate ----------------------------------------------
    results: list[dict[str, Any]] = []
    for idx, cand in enumerate(candidates):
        semantic_score = float(all_semantic_scores[idx])
        momentum = calculate_momentum_score(cand, momentum_config)

        final_score = (
            semantic_score * weights.get("semantic", 0.7)
            + momentum * weights.get("momentum", 0.3)
        )

        results.append(
            {
                "id": cand.get("id", f"unknown_{idx}"),
                "name": cand.get("name", "Unknown"),
                "role": cand.get("role", "N/A"),
                "resume_text": cand.get("resume_text", ""),
                "final_score": round(final_score, 3),
                "semantic_score": round(semantic_score, 3),
                "momentum_score": momentum,
                "raw_data": cand,
            }
        )

    results.sort(key=lambda x: x["final_score"], reverse=True)
    logger.info("Ranking complete – top candidate: %s", results[0]["name"] if results else "N/A")
    return results
