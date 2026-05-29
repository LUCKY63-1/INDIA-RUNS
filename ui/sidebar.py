"""
Sidebar UI — data management, filters, weight configuration.
"""
from __future__ import annotations

import hashlib
import os
from typing import Any

import streamlit as st

from config.weights import ALL_WEIGHT_KEYS, MOMENTUM_WEIGHTS, WEIGHT_PRESETS
from data.loader import (
    load_json,
    load_uploaded_csv,
    load_uploaded_json,
    parse_docx,
    parse_pdf,
    save_json,
)
from data.resume_ingest import build_candidate_from_resume_text


def _get_data_dir() -> str:
    base = os.path.dirname(os.path.dirname(__file__))
    d = os.path.join(base, "data")
    if not os.path.isdir(d):
        d = os.path.join(base, "ai-recruiter-poc", "data")
    return d


def render_sidebar() -> dict[str, Any]:
    """
    Render the full sidebar and return a context dict with:
    - weights, momentum_config
    - filter values
    - api_key
    """
    data_dir = _get_data_dir()

    # ── Data Management ──────────────────────────────────────────────────
    st.sidebar.markdown(
        """
        <div style="
            padding: 10px 0 8px 0;
            border-bottom: 2px solid #5C6BC040;
            margin-bottom: 4px;
        ">
            <span style="font-size:1.05rem; font-weight:800; color:#5C6BC0;">
                📁 Data Management
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Candidate Filters
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<span style="font-weight:700; color:#1E2A38; font-size:0.9rem;">🔍 Candidate Filters</span>',
        unsafe_allow_html=True,
    )
    filter_role = st.sidebar.text_input("Role contains", value="")
    filter_skill = st.sidebar.text_input("Skill or keyword in resume", value="")
    filter_min_commits = st.sidebar.number_input("Min GitHub commits (90d)", 0, 10000, 0)
    filter_min_certs = st.sidebar.number_input("Min certifications (1y)", 0, 100, 0)
    filter_min_skills = st.sidebar.number_input("Min new skills (180d)", 0, 100, 0)
    filter_location = st.sidebar.text_input("Location (optional)", value="")

    # 1. Dataset Selection
    data_files = sorted(
        f
        for f in os.listdir(data_dir)
        if f.endswith(".json") and f != "job_descriptions.json"
    )
    selected_file = st.sidebar.selectbox("Select Preset Dataset", data_files)

    if st.sidebar.button("Load Preset Dataset"):
        path = os.path.join(data_dir, selected_file)
        st.session_state.active_dataset_path = path
        st.session_state.candidates = load_json(path)
        st.sidebar.success(f"Loaded {len(st.session_state.candidates)} candidates!")

    # 2. File Upload (CSV / JSON / PDF / DOCX)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Upload Custom Data")
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV, JSON, PDF or DOCX",
        type=["csv", "json", "pdf", "docx"],
    )

    def _candidate_dataset_path() -> str:
        active_path = st.session_state.get("active_dataset_path")
        if active_path:
            return str(active_path)
        path = os.path.join(data_dir, "candidates.json")
        st.session_state.active_dataset_path = path
        return path

    def _persist_uploaded_candidate(candidate: dict[str, Any]) -> None:
        path = _candidate_dataset_path()
        current_candidates = st.session_state.candidates
        if not isinstance(current_candidates, list) or not current_candidates:
            current_candidates = load_json(path)
            if not isinstance(current_candidates, list):
                current_candidates = []

        current_candidates.append(candidate)
        st.session_state.candidates = current_candidates

        if save_json(path, current_candidates):
            st.session_state._needs_rank_refresh = True
            st.sidebar.success(
                f"Added {candidate.get('name', 'candidate')} and saved to {os.path.basename(path)}!"
            )
            st.rerun()

        st.sidebar.error("Could not save the uploaded candidate to JSON.")

    if uploaded_file is not None:
        name_lower = uploaded_file.name.lower()
        if name_lower.endswith(".json"):
            st.session_state.candidates = load_uploaded_json(uploaded_file)
            st.session_state.active_dataset_path = None
            st.sidebar.success(f"Uploaded {len(st.session_state.candidates)} candidates!")
        elif name_lower.endswith(".csv"):
            st.session_state.candidates = load_uploaded_csv(uploaded_file)
            st.session_state.active_dataset_path = None
            st.sidebar.success(f"Uploaded {len(st.session_state.candidates)} candidates!")
        elif name_lower.endswith(".pdf"):
            upload_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
            if st.session_state.get("_resume_upload_hash") != upload_hash:
                st.session_state["_resume_upload_hash"] = upload_hash
                text = parse_pdf(uploaded_file)
                if text:
                    st.session_state["_uploaded_resume_text"] = text
                    candidate = build_candidate_from_resume_text(text, uploaded_file.name)
                    if candidate:
                        _persist_uploaded_candidate(candidate)
                    else:
                        st.sidebar.error("Could not build a candidate from the PDF text.")
                else:
                    st.sidebar.error("Could not extract text from PDF.")
        elif name_lower.endswith(".docx"):
            upload_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
            if st.session_state.get("_resume_upload_hash") != upload_hash:
                st.session_state["_resume_upload_hash"] = upload_hash
                text = parse_docx(uploaded_file)
                if text:
                    st.session_state["_uploaded_resume_text"] = text
                    candidate = build_candidate_from_resume_text(text, uploaded_file.name)
                    _persist_uploaded_candidate(candidate)
                else:
                    st.sidebar.error("Could not extract text from DOCX.")

    # 3. Manual Entry
    st.sidebar.markdown("---")
    st.sidebar.subheader("Add Candidate Manually")
    with st.sidebar.form("manual_entry_form"):
        new_name = st.text_input("Name")
        new_role = st.text_input("Role")

        # Pre-fill resume text from PDF/DOCX upload if available
        prefill = st.session_state.pop("_uploaded_resume_text", "")
        new_resume = st.text_area("Resume Text", value=prefill)

        col1, col2 = st.columns(2)
        new_github = col1.number_input("GitHub Commits (90d)", 0, 1000, 0)
        new_jobs = col2.number_input("Job Changes (2y)", 0, 10, 0)
        new_certs = col1.number_input("Certs (1y)", 0, 20, 0)
        new_linkedin = col2.number_input("LinkedIn Posts (30d)", 0, 100, 0)
        new_growth = col1.number_input("New Skills (180d)", 0, 50, 0)

        submit_button = st.form_submit_button("Add Candidate")
        if submit_button:
            # Validation
            if not new_name.strip() or not new_role.strip():
                st.error("❌ Name and Role are required.")
            elif not new_resume.strip():
                st.error("❌ Resume text is required.")
            else:
                new_cand = {
                    "id": f"manual_{len(st.session_state.candidates) + 1}",
                    "name": new_name.strip(),
                    "role": new_role.strip(),
                    "resume_text": new_resume.strip(),
                    "github_commits_last_90d": new_github,
                    "job_changes_last_2y": new_jobs,
                    "certifications_last_year": new_certs,
                    "linkedin_posts_last_30d": new_linkedin,
                    "skills_acquired_last_180d": new_growth,
                }
                st.session_state.candidates.append(new_cand)
                if st.session_state.active_dataset_path:
                    ok = save_json(
                        st.session_state.active_dataset_path,
                        st.session_state.candidates,
                    )
                    if ok:
                        st.session_state._needs_rank_refresh = True
                        st.success(
                            f"Added {new_name} and saved to "
                            f"{os.path.basename(st.session_state.active_dataset_path)}!"
                        )
                        st.rerun()
                    else:
                        st.error(f"Added {new_name}, but file save failed.")
                else:
                    st.warning(
                        f"Added {new_name} in session only. "
                        "Load a preset dataset first to save to a file."
                    )

    # ── Ranking Weights ──────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Ranking Weights")

    api_key = st.sidebar.text_input(
        "Groq API Key (UI only)",
        type="password",
        key="api_key",
        help="Paste the key here when you want LLM explanations. If empty, the app uses the fallback explanation.",
    )

    if st.sidebar.button("Reset to Default"):
        for k, v in ALL_WEIGHT_KEYS.items():
            st.session_state[k] = v
        st.session_state.api_key = ""
        st.rerun()

    # Weight Presets
    st.sidebar.subheader("Weight Presets")
    preset_cols = st.sidebar.columns(len(WEIGHT_PRESETS))
    for i, (preset_name, preset_vals) in enumerate(WEIGHT_PRESETS.items()):
        if preset_cols[i].button(preset_name):
            for k, v in preset_vals.items():
                st.session_state[k] = v
            st.rerun()

    # Main Weights
    st.sidebar.subheader("Main Weights")
    semantic_w = st.sidebar.slider(
        "Semantic (Matching)", 0.0, 1.0, st.session_state.semantic, key="semantic"
    )
    momentum_w = st.sidebar.slider(
        "Momentum (Activity)", 0.0, 1.0, st.session_state.momentum, key="momentum"
    )
    weights = {"semantic": semantic_w, "momentum": momentum_w}

    # Momentum Sub-Weights
    st.sidebar.subheader("Momentum Signal Tuning")
    mw_github = st.sidebar.slider("GitHub Weight", 0.0, 1.0, st.session_state.github, key="github")
    mw_linkedin = st.sidebar.slider(
        "LinkedIn Weight", 0.0, 1.0, st.session_state.linkedin, key="linkedin"
    )
    mw_certs = st.sidebar.slider("Certs Weight", 0.0, 1.0, st.session_state.certs, key="certs")
    mw_growth = st.sidebar.slider(
        "Growth Velocity", 0.0, 1.0, st.session_state.growth, key="growth"
    )
    mw_stability = st.sidebar.slider(
        "Stability/Movement", 0.0, 1.0, st.session_state.stability, key="stability"
    )

    momentum_config = {
        "github": mw_github,
        "linkedin": mw_linkedin,
        "certs": mw_certs,
        "growth": mw_growth,
        "stability": mw_stability,
    }

    # ── Weight normalisation indicator ───────────────────────────────────
    total_momentum_w = sum(momentum_config.values())
    if abs(total_momentum_w - 1.0) > 0.01:
        st.sidebar.warning(
            f"⚖️ Momentum sub-weights sum to **{total_momentum_w:.2f}** "
            f"(ideal = 1.0). Scores may be scaled unexpectedly."
        )
    else:
        st.sidebar.success("⚖️ Momentum sub-weights sum to 1.0 ✓")

    return {
        "weights": weights,
        "momentum_config": momentum_config,
        "api_key": api_key,
        "data_dir": data_dir,
        "filters": {
            "role": filter_role,
            "skill": filter_skill,
            "min_commits": filter_min_commits,
            "min_certs": filter_min_certs,
            "min_skills": filter_min_skills,
            "location": filter_location,
        },
    }
