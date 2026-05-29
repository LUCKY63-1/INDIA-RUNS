"""
Shortlist — role-specific shortlisting and CSV export.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_shortlist(
    available_roles: list[str],
) -> None:
    """Render shortlist creation controls and display current shortlist."""
    st.markdown("---")
    st.markdown("### 📋 Shortlist by Role")

    role_options = ["Any"] + available_roles
    shortlist_role = st.selectbox("Role to shortlist", role_options)
    top_n = st.number_input("Top N to shortlist", min_value=1, max_value=100, value=3)

    if st.button("Create Shortlist"):
        src = st.session_state.get("last_results", [])
        if shortlist_role != "Any":
            src = [r for r in src if r.get("role") == shortlist_role]
        shortlist = src[:top_n]
        st.session_state.shortlist = shortlist
        st.success(f"Shortlisted {len(shortlist)} candidates for role: {shortlist_role}")
        if shortlist:
            df_short = pd.DataFrame(shortlist)[
                ["id", "name", "role", "final_score", "semantic_score", "momentum_score"]
            ]
            csv_s = df_short.to_csv(index=False)
            st.download_button(
                "Download Shortlist CSV",
                csv_s,
                file_name="shortlist.csv",
                mime="text/csv",
            )

    # Display current shortlist if exists
    if st.session_state.get("shortlist"):
        with st.expander("View Current Shortlist"):
            st.table(
                pd.DataFrame(st.session_state.shortlist)[
                    ["id", "name", "role", "final_score"]
                ]
            )
