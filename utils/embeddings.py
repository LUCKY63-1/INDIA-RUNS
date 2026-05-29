"""
Semantic embedding utilities using Sentence-Transformers.
"""
from __future__ import annotations

import logging
from typing import Union

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Return a cached SentenceTransformer model (lazy-loaded on first call)."""
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2' …")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded successfully.")
    return _model


def get_embeddings(texts: list[str]) -> np.ndarray:
    """Encode a list of texts into embedding vectors."""
    model = get_model()
    return model.encode(texts)
