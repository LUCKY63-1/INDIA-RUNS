"""
Single source of truth for all ranking weight defaults and presets.
"""

# ---------------------------------------------------------------------------
# Main ranking weights
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS: dict[str, float] = {
    "semantic": 0.6,
    "momentum": 0.4,
}

# ---------------------------------------------------------------------------
# Momentum sub-signal weights
# ---------------------------------------------------------------------------
MOMENTUM_WEIGHTS: dict[str, float] = {
    "github": 0.2,
    "linkedin": 0.2,
    "certs": 0.2,
    "growth": 0.2,
    "stability": 0.2,
}

# ---------------------------------------------------------------------------
# Convenience: all weight keys used in session state
# ---------------------------------------------------------------------------
ALL_WEIGHT_KEYS: dict[str, float] = {**DEFAULT_WEIGHTS, **MOMENTUM_WEIGHTS}

# ---------------------------------------------------------------------------
# Named presets that users can activate with one click
# ---------------------------------------------------------------------------
WEIGHT_PRESETS: dict[str, dict[str, float]] = {
    "Balanced": {**ALL_WEIGHT_KEYS},
    "Aggressive Hiring": {
        "semantic": 0.3,
        "momentum": 0.7,
        "github": 0.4,
        "linkedin": 0.3,
        "certs": 0.1,
        "growth": 0.6,
        "stability": 0.2,
    },
    "Quality Focus": {
        "semantic": 0.85,
        "momentum": 0.15,
        "github": 0.1,
        "linkedin": 0.05,
        "certs": 0.3,
        "growth": 0.05,
        "stability": 0.45,
    },
}
