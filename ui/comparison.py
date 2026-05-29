"""
Side-by-side candidate comparison with radar charts.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go  # type: ignore[import-untyped]
import streamlit as st

from core.explanation import generate_explanation


def _radar_chart(candidate: dict[str, Any]) -> go.Figure:
    """Build a radar chart of the 5 momentum signals for a candidate."""
    raw = candidate.get("raw_data", candidate)
    categories = ["GitHub", "LinkedIn", "Certs", "Growth", "Stability"]

    # Normalise to 0-1 for consistent display
    github = min(raw.get("github_commits_last_90d", 0) / 100, 1.0)
    linkedin = min(raw.get("linkedin_posts_last_30d", 0) / 20, 1.0)
    certs = min(raw.get("certifications_last_year", 0) / 5, 1.0)
    growth = min(raw.get("skills_acquired_last_180d", 0) / 10, 1.0)
    changes = raw.get("job_changes_last_2y", 0)
    stability = 1.0 if 1 <= changes <= 2 else (0.5 if changes == 0 else 0.3)

    values = [github, linkedin, certs, growth, stability]
    values.append(values[0])  # close the polygon
    cats = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(r=values, theta=cats, fill="toself", name=candidate["name"])
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30),
        height=280,
    )
    return fig


def render_comparison(
    results: list[dict[str, Any]],
    job_description: str,
    api_key: str | None = None,
    top_n: int = 3,
) -> None:
    """Render side-by-side comparison of the top N candidates."""
    if not results:
        return

    compare = st.checkbox("🔍 Compare top candidates side-by-side")
    if not compare:
        return

    topn = results[:top_n]
    cols = st.columns(len(topn))

    for i, cand in enumerate(topn):
        with cols[i]:
            st.markdown(f"### #{i + 1} {cand['name']}")
            st.markdown(f"**Role:** {cand['role']}")

            explanation = generate_explanation(
                cand, job_description, cand, api_key=api_key
            )
            st.write(explanation)

            # Score table
            st.write(
                pd.DataFrame(
                    {
                        "Metric": ["Final", "Semantic", "Momentum"],
                        "Value": [
                            cand["final_score"],
                            cand["semantic_score"],
                            cand["momentum_score"],
                        ],
                    }
                ).set_index("Metric")
            )

            # Radar chart
            st.plotly_chart(_radar_chart(cand), use_container_width=True)
