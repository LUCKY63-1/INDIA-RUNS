"""
Leaderboard — ranked results display with per-candidate details.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from core.explanation import generate_explanation
from core.skills import analyse_skill_gap


# ── Helpers ───────────────────────────────────────────────────────────────────

def _score_meta(score: float) -> tuple[str, str, str]:
    """Return (hex_color, bg_hex, tier_label) for a given score."""
    if score >= 0.75:
        return "#2D7D46", "#EBF5EE", "Excellent"
    if score >= 0.50:
        return "#1565C0", "#E3EEF9", "Good"
    if score >= 0.30:
        return "#E06B00", "#FFF3E0", "Fair"
    return "#C0392B", "#FDECEA", "Low"


def _rank_badge_html(rank: int, color: str, bg: str) -> str:
    return (
        f'<div style="background:{bg}; color:{color}; border:1.5px solid {color}; '
        f'border-radius:50%; width:32px; height:32px; display:flex; align-items:center; '
        f'justify-content:center; font-weight:800; font-size:13px; flex-shrink:0;">'
        f"{rank}</div>"
    )


def _tier_badge_html(tier: str, color: str, bg: str) -> str:
    return (
        f'<span style="background:{bg}; color:{color}; border:1px solid {color}40; '
        f'padding:2px 9px; border-radius:12px; font-size:11px; font-weight:700; '
        f'letter-spacing:0.3px;">{tier}</span>'
    )


def _score_pill_html(score: float, color: str, bg: str) -> str:
    return (
        f'<div style="text-align:right;">'
        f'<span style="font-size:1.5rem; font-weight:800; color:{color};">{score:.3f}</span><br>'
        f'<span style="font-size:11px; color:#6B7280; font-weight:500;">score</span>'
        f"</div>"
    )


# ── Main render ───────────────────────────────────────────────────────────────

def render_leaderboard(
    results: list[dict[str, Any]],
    job_description: str,
    api_key: str | None = None,
) -> None:
    """Render the ranked leaderboard with styled, expandable candidate cards."""
    if not results:
        st.info("No results to display.")
        return

    st.markdown(
        '<h3 style="margin-top:1.5rem; margin-bottom:0.5rem;">🏆 Leaderboard</h3>',
        unsafe_allow_html=True,
    )

    for idx, res in enumerate(results):
        score = res["final_score"]
        color, bg, tier = _score_meta(score)

        # Expander header with visual score hint
        expander_label = (
            f"{'🥇' if idx == 0 else ('🥈' if idx == 1 else ('🥉' if idx == 2 else f'#{idx+1}'))}  "
            f"{res['name']}  ·  {tier}  ({score:.3f})"
        )

        with st.expander(expander_label, expanded=(idx == 0)):

            # ── Card header row ─────────────────────────────────────────────
            st.markdown(
                f"""
                <div style="
                    display:flex; align-items:center; gap:14px;
                    background:{bg}; border:1px solid {color}30;
                    border-radius:10px; padding:14px 18px; margin-bottom:12px;
                ">
                    {_rank_badge_html(idx + 1, color, bg)}
                    <div style="flex:1; min-width:0;">
                        <div style="font-size:1.05rem; font-weight:700; color:#1E2A38;">
                            {res['name']}
                        </div>
                        <div style="font-size:0.87rem; color:#6B7280; margin-top:2px;">
                            {res.get('role', '—')}
                            &nbsp;&nbsp;{_tier_badge_html(tier, color, bg)}
                        </div>
                    </div>
                    {_score_pill_html(score, color, bg)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns([2, 1])

            with c1:
                # Explanation
                explanation = generate_explanation(
                    res, job_description, res, api_key=api_key
                )
                st.write(explanation)

                # Skill gap analysis
                gap = analyse_skill_gap(res.get("raw_data", res), job_description)
                if gap.matched or gap.missing:
                    st.markdown("---")
                    st.markdown("**🎯 Skill Analysis**")
                    st.metric("Skill Overlap", f"{gap.overlap_pct}%")
                    if gap.matched:
                        st.markdown(
                            "✅ **Matched:** " + ", ".join(f"`{s}`" for s in gap.matched)
                        )
                    if gap.missing:
                        st.markdown(
                            "❌ **Missing:** " + ", ".join(f"`{s}`" for s in gap.missing)
                        )
                    if gap.extra:
                        st.markdown(
                            "➕ **Extra:** " + ", ".join(f"`{s}`" for s in gap.extra)
                        )

            with c2:
                # Score breakdown chart
                semantic_color, semantic_bg, _ = _score_meta(res["semantic_score"])
                momentum_color, momentum_bg, _ = _score_meta(res["momentum_score"])

                st.markdown(
                    f"""
                    <div style="
                        background:#F8F9FC; border:1px solid #DDE0EC;
                        border-radius:10px; padding:14px; margin-bottom:10px;
                    ">
                        <div style="font-size:0.75rem; font-weight:700; color:#6B7280;
                                    text-transform:uppercase; letter-spacing:0.4px; margin-bottom:10px;">
                            Score Breakdown
                        </div>
                        <div style="margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between;
                                        font-size:0.82rem; color:#1E2A38; margin-bottom:3px;">
                                <span>Semantic Match</span>
                                <span style="font-weight:700; color:{semantic_color};">
                                    {res['semantic_score']:.3f}
                                </span>
                            </div>
                            <div style="background:#E8EAF0; border-radius:4px; height:6px; overflow:hidden;">
                                <div style="width:{min(res['semantic_score']*100,100):.0f}%;
                                            background:{semantic_color}; height:100%;
                                            border-radius:4px;"></div>
                            </div>
                        </div>
                        <div>
                            <div style="display:flex; justify-content:space-between;
                                        font-size:0.82rem; color:#1E2A38; margin-bottom:3px;">
                                <span>Momentum</span>
                                <span style="font-weight:700; color:{momentum_color};">
                                    {res['momentum_score']:.3f}
                                </span>
                            </div>
                            <div style="background:#E8EAF0; border-radius:4px; height:6px; overflow:hidden;">
                                <div style="width:{min(res['momentum_score']*100,100):.0f}%;
                                            background:{momentum_color}; height:100%;
                                            border-radius:4px;"></div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                raw = res.get("raw_data", {})
                st.write(
                    f"📈 **Growth Velocity:** "
                    f"{raw.get('skills_acquired_last_180d', 0)} new skills"
                )

                # Weak signals
                weak: list[str] = []
                if res["semantic_score"] < 0.4:
                    weak.append("Low semantic match")
                if res["momentum_score"] < 0.2:
                    weak.append("Low momentum signals")
                if raw.get("github_commits_last_90d", 0) < 10:
                    weak.append("Low GitHub activity")
                if raw.get("certifications_last_year", 0) == 0:
                    weak.append("No recent certifications")
                if raw.get("skills_acquired_last_180d", 0) == 0:
                    weak.append("No recent skill growth")
                if weak:
                    st.markdown(
                        "<div style='margin-top:8px;'>"
                        "<span style='font-size:0.8rem; font-weight:700; color:#E06B00;'>⚠️ Weak Signals</span>"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    for w in weak:
                        st.markdown(
                            f"<span style='font-size:0.82rem; color:#6B7280;'>• {w}</span>",
                            unsafe_allow_html=True,
                        )

            # Delete candidate button (subtle, at bottom)
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            if st.button(f"🗑️ Remove {res['name']}", key=f"del_{res['id']}"):
                st.session_state.candidates = [
                    c
                    for c in st.session_state.candidates
                    if c.get("id") != res["id"]
                ]
                st.success(f"Removed {res['name']}.")
                st.rerun()
