"""
Analytics dashboard — distribution charts and scatter plots for ranking results.
"""
from __future__ import annotations

from typing import Any

import plotly.express as px  # type: ignore[import-untyped]
import plotly.graph_objects as go  # type: ignore[import-untyped]
import streamlit as st


def render_analytics(results: list[dict[str, Any]]) -> None:
    """Render an analytics tab with score distributions and scatter plots."""
    if not results:
        return

    with st.expander("📊 Analytics Dashboard", expanded=False):
        tab1, tab2, tab3 = st.tabs(
            ["Score Distributions", "Semantic vs Momentum", "Signal Breakdown"]
        )

        # ── Tab 1: Histograms ────────────────────────────────────────────
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.histogram(
                    [r["semantic_score"] for r in results],
                    nbins=15,
                    title="Semantic Score Distribution",
                    labels={"value": "Semantic Score", "count": "Candidates"},
                    color_discrete_sequence=["#636EFA"],
                )
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.histogram(
                    [r["momentum_score"] for r in results],
                    nbins=15,
                    title="Momentum Score Distribution",
                    labels={"value": "Momentum Score", "count": "Candidates"},
                    color_discrete_sequence=["#EF553B"],
                )
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)

        # ── Tab 2: Scatter ───────────────────────────────────────────────
        with tab2:
            fig = px.scatter(
                x=[r["semantic_score"] for r in results],
                y=[r["momentum_score"] for r in results],
                text=[r["name"] for r in results],
                size=[r["final_score"] for r in results],
                title="Semantic Match vs Momentum",
                labels={"x": "Semantic Score", "y": "Momentum Score"},
                color=[r["final_score"] for r in results],
                color_continuous_scale="Viridis",
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

        # ── Tab 3: Per-candidate signal breakdown ────────────────────────
        with tab3:
            selected_name = st.selectbox(
                "Select candidate",
                [r["name"] for r in results],
                key="analytics_candidate",
            )
            selected = next(r for r in results if r["name"] == selected_name)
            raw = selected.get("raw_data", {})

            categories = ["GitHub", "LinkedIn", "Certs", "Growth", "Stability"]
            github = min(raw.get("github_commits_last_90d", 0) / 100, 1.0)
            linkedin = min(raw.get("linkedin_posts_last_30d", 0) / 20, 1.0)
            certs = min(raw.get("certifications_last_year", 0) / 5, 1.0)
            growth = min(raw.get("skills_acquired_last_180d", 0) / 10, 1.0)
            changes = raw.get("job_changes_last_2y", 0)
            stability = 1.0 if 1 <= changes <= 2 else (0.5 if changes == 0 else 0.3)
            values = [github, linkedin, certs, growth, stability]

            fig = go.Figure()
            fig.add_trace(
                go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=selected_name,
                )
            )
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=False,
                title=f"Signal Breakdown — {selected_name}",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Raw numbers
            st.markdown("**Raw Activity Data:**")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("GitHub", raw.get("github_commits_last_90d", 0))
            col2.metric("LinkedIn", raw.get("linkedin_posts_last_30d", 0))
            col3.metric("Certs", raw.get("certifications_last_year", 0))
            col4.metric("New Skills", raw.get("skills_acquired_last_180d", 0))
            col5.metric("Job Changes", raw.get("job_changes_last_2y", 0))
