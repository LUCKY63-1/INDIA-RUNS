"""
Empty state — rich getting-started card shown when no candidates are loaded.
"""
from __future__ import annotations

import os
from typing import Any

import streamlit as st

from data.loader import load_json


def render_empty_state(data_dir: str) -> None:
    """Show a helpful onboarding card when the candidate list is empty."""
    st.markdown("---")
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 1rem;
            color: white;
            text-align: center;
        ">
            <h2 style="color: white; margin-bottom: 0.5rem;">👋 Welcome to AI Recruiter</h2>
            <p style="font-size: 1.1rem; opacity: 0.9;">
                Get started by loading a dataset or uploading your own candidates.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 1️⃣ Load Sample Data")
        st.markdown(
            "Click the button below to instantly load the built-in candidate dataset "
            "and start exploring."
        )
        if st.button("🚀 Load Sample Data", key="empty_state_load"):
            path = os.path.join(data_dir, "candidates.json")
            if os.path.isfile(path):
                st.session_state.candidates = load_json(path)
                st.session_state.active_dataset_path = path
                st.success(f"Loaded {len(st.session_state.candidates)} candidates!")
                st.rerun()
            else:
                st.error("Sample data file not found.")

    with col2:
        st.markdown("### 2️⃣ Upload Your Own")
        st.markdown(
            "Use the sidebar to upload a **CSV** or **JSON** file with your "
            "candidate data, or a **PDF / DOCX** resume."
        )

    with col3:
        st.markdown("### 3️⃣ Add Manually")
        st.markdown(
            "Use the sidebar form to add candidates one by one. "
            "Fill in the name, role, resume text, and activity signals."
        )

    # Sample data preview
    with st.expander("📄 Preview: What candidate data looks like"):
        st.json(
            {
                "id": "c1",
                "name": "Alice Chen",
                "role": "Senior Software Engineer",
                "resume_text": "Senior Software Engineer with 8 years of experience in Python, React, and AWS.",
                "github_commits_last_90d": 120,
                "job_changes_last_2y": 0,
                "certifications_last_year": 2,
                "linkedin_posts_last_30d": 5,
                "skills_acquired_last_180d": 3,
            }
        )
