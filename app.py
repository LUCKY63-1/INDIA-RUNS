"""
AI Recruiter POC — Streamlit entry point.

This slim orchestrator wires together the sidebar, ranking engine, and
UI components. All heavy logic lives in core/ and ui/ modules.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv  # type: ignore[import-untyped]

from config.weights import ALL_WEIGHT_KEYS
from core.filters import filter_candidates
from core.history import save_snapshot, list_snapshots, load_snapshot
from core.profile import infer_dataset_profile, suggest_job_titles
from core.ranking import rank_candidates
from data.loader import load_json
from ui.analytics import render_analytics
from ui.comparison import render_comparison
from ui.empty_state import render_empty_state
from ui.leaderboard import render_leaderboard
from ui.shortlist import render_shortlist
from ui.sidebar import render_sidebar

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")

st.set_page_config(page_title="AI Recruiter POC", layout="wide", page_icon="🤖")

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Typography ────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }

    /* ── Page title ────────────────────────────────────────────────────── */
    h1 {
        background: linear-gradient(135deg, #5C6BC0 0%, #7E57C2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    h2, h3 {
        color: #1E2A38 !important;
        font-weight: 700 !important;
    }

    /* ── Metric cards ───────────────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #DDE0EC;
        border-radius: 12px;
        padding: 16px 20px !important;
        box-shadow: 0 2px 10px rgba(92, 107, 192, 0.08);
    }
    [data-testid="metric-container"] label {
        color: #6B7280 !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #1E2A38 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }

    /* ── Primary buttons ────────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #5C6BC0 0%, #7E57C2 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.2rem !important;
        transition: box-shadow 0.2s ease, transform 0.15s ease !important;
        box-shadow: 0 2px 10px rgba(92, 107, 192, 0.28) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 18px rgba(92, 107, 192, 0.38) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Download buttons ───────────────────────────────────────────────── */
    [data-testid="stDownloadButton"] > button {
        background: #ffffff !important;
        color: #5C6BC0 !important;
        border: 1.5px solid #5C6BC0 !important;
        box-shadow: none !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: #5C6BC0 !important;
        color: #ffffff !important;
        transform: none !important;
    }

    /* ── Expanders ──────────────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        border: 1px solid #DDE0EC !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background: #ffffff;
    }
    [data-testid="stExpander"] summary {
        font-weight: 600 !important;
        color: #1E2A38 !important;
        padding: 12px 16px !important;
    }
    [data-testid="stExpander"] summary:hover {
        background: #F4F5FB !important;
    }

    /* ── Tabs ───────────────────────────────────────────────────────────── */
    [data-testid="stTabs"] [role="tab"] {
        border-radius: 8px 8px 0 0 !important;
        font-weight: 600 !important;
        color: #6B7280 !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #5C6BC0 !important;
        border-bottom: 2px solid #5C6BC0 !important;
    }

    /* ── DataFrames ─────────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid #DDE0EC !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    /* ── Sidebar ────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #FAFBFF !important;
        border-right: 1px solid #DDE0EC !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: #ffffff !important;
        color: #5C6BC0 !important;
        border: 1.5px solid #5C6BC0 !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #5C6BC0 0%, #7E57C2 100%) !important;
        color: #ffffff !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* ── Alerts / info boxes ────────────────────────────────────────────── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border: 1px solid transparent !important;
    }

    /* ── Selectbox & multiselect ────────────────────────────────────────── */
    [data-baseweb="select"] > div {
        border-radius: 8px !important;
        border-color: #DDE0EC !important;
    }

    /* ── Text inputs ────────────────────────────────────────────────────── */
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div {
        border-radius: 8px !important;
        border-color: #DDE0EC !important;
    }

    /* ── Horizontal dividers ────────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid #DDE0EC !important;
        margin: 1.2rem 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "active_dataset_path" not in st.session_state:
    st.session_state.active_dataset_path = None
if "ranking_runs" not in st.session_state:
    st.session_state.ranking_runs = 0
if "total_candidates_processed" not in st.session_state:
    st.session_state.total_candidates_processed = 0
if "total_ranking_time" not in st.session_state:
    st.session_state.total_ranking_time = 0.0
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "last_job" not in st.session_state:
    st.session_state.last_job = None
if "shortlist" not in st.session_state:
    st.session_state.shortlist = []

for weight_key, default_value in ALL_WEIGHT_KEYS.items():
    if weight_key not in st.session_state:
        st.session_state[weight_key] = default_value

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🚀 AI Recruiter POC")
st.markdown(
    """
    <div style="
        display:flex; align-items:center; gap:12px;
        background: linear-gradient(135deg, #5C6BC015 0%, #7E57C215 100%);
        border: 1px solid #DDE0EC;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 8px;
    ">
        <span style="font-size:1.4rem;">📈</span>
        <div>
            <span style="font-weight:700; color:#1E2A38; font-size:1rem;">
                Advanced Momentum Scoring
            </span>
            <span style="color:#6B7280; font-size:0.88rem; margin-left:8px;">
                Growth Velocity · GitHub · LinkedIn · Certs · Stability
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar (returns weights, filters, api_key, data_dir)
# ---------------------------------------------------------------------------
ctx = render_sidebar()
weights = ctx["weights"]
momentum_config = ctx["momentum_config"]
api_key = ctx["api_key"]
data_dir = ctx["data_dir"]
filters = ctx["filters"]

# ---------------------------------------------------------------------------
# Job Selection (multi-job support)
# ---------------------------------------------------------------------------
job_file = os.path.join(data_dir, "job_descriptions.json")
jobs_data = load_json(job_file)
if not jobs_data:
    st.error("No job descriptions found. Check data/job_descriptions.json.")
    st.stop()

job_titles = [j["title"] for j in jobs_data]

dataset_profile = infer_dataset_profile(
    st.session_state.candidates,
    str(st.session_state.get("active_dataset_path", "")),
)
suggested_job_titles = suggest_job_titles(dataset_profile, jobs_data)
stored_profile = st.session_state.get("job_select_profile")
stored_selection = st.session_state.get("job_select", [])
valid_selection = [title for title in stored_selection if title in job_titles]

if stored_profile != dataset_profile or not valid_selection:
    st.session_state.job_select = suggested_job_titles
    st.session_state.job_select_profile = dataset_profile

selected_job_titles = st.multiselect(
    "Select Target Job Description(s)",
    job_titles,
    default=[job_titles[0]] if job_titles else [],
    key="job_select",
)
st.caption(f"Auto-matched profile: {dataset_profile.title()} | Suggested: {', '.join(suggested_job_titles) if suggested_job_titles else 'None'}")
if not selected_job_titles:
    st.warning("Please select at least one job description.")
    st.stop()

selected_jobs = [j for j in jobs_data if j["title"] in selected_job_titles]

# Show job descriptions
for job in selected_jobs:
    with st.expander(f"📄 {job['title']}"):
        st.write(job["description"])

# Display the current momentum formula
mw = momentum_config
st.markdown("### 🧪 Current Momentum Formula")
st.latex(
    rf"\text{{Score}} = \Big("
    rf"{mw['github']} \times \text{{GitHub}} + "
    rf"{mw['linkedin']} \times \text{{LinkedIn}} + "
    rf"{mw['certs']} \times \text{{Certs}} + "
    rf"{mw['growth']} \times \text{{Growth}} + "
    rf"{mw['stability']} \times \text{{Stability}}"
    rf"\Big) \times \text{{Recency}}"
)

with st.expander("How scoring works"):
    st.markdown(
        """
        - **Semantic score** measures how closely the resume matches the job description.
        - **Momentum score** combines activity signals like GitHub, LinkedIn, certifications, skill growth, and movement.
        - **Skill analysis** extracts named skills from resumes and compares them to job requirements.
        - **Final score** blends semantic and momentum weights, then ranks candidates from highest to lowest.
        """
    )


# ---------------------------------------------------------------------------
# Helper: available roles
# ---------------------------------------------------------------------------
def get_available_roles() -> list[str]:
    roles = {c.get("role") for c in st.session_state.candidates if c.get("role")}
    return sorted(roles) if roles else sorted(set(job_titles))


def run_ranking_pipeline() -> None:
    """Filter candidates and update ranking outputs for the selected jobs."""
    # Filter candidates first (outside spinner for fast feedback)
    filtered = filter_candidates(
        st.session_state.candidates,
        role=filters["role"],
        skill=filters["skill"],
        min_commits=filters["min_commits"],
        min_certs=filters["min_certs"],
        min_skills=filters["min_skills"],
        location=filters["location"],
    )

    if not filtered:
        st.warning("No candidates match the current filters.")
        return

    with st.spinner("Processing…"):
        start_time = time.perf_counter()

        # Multi-job ranking
        if len(selected_jobs) == 1:
            # Single job — classic view
            results = rank_candidates(
                selected_jobs[0]["description"],
                filtered,
                weights,
                momentum_config=momentum_config,
            )
            st.session_state.last_results = results
            st.session_state.last_job = selected_jobs[0]

            # Save snapshot
            save_snapshot(
                selected_jobs[0]["title"],
                results,
                weights,
                momentum_config,
            )
        else:
            # Multi-job matrix
            all_job_results: dict[str, list[dict[str, Any]]] = {}
            for job in selected_jobs:
                job_results = rank_candidates(
                    job["description"],
                    filtered,
                    weights,
                    momentum_config=momentum_config,
                )
                all_job_results[job["title"]] = job_results
                save_snapshot(job["title"], job_results, weights, momentum_config)

            # Use first job as primary results for leaderboard
            results = all_job_results[selected_jobs[0]["title"]]
            st.session_state.last_results = results
            st.session_state.last_job = selected_jobs[0]
            st.session_state.all_job_results = all_job_results

        elapsed = time.perf_counter() - start_time

        # Update cumulative stats
        st.session_state.ranking_runs += 1
        st.session_state.total_candidates_processed += len(filtered)
        st.session_state.total_ranking_time += elapsed


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------
if not st.session_state.candidates:
    render_empty_state(data_dir)
else:
    # ── Ranking ──────────────────────────────────────────────────────────
    refresh_after_upload = bool(st.session_state.pop("_needs_rank_refresh", False))
    if st.button("🚀 Run AI Ranking") or refresh_after_upload:
        run_ranking_pipeline()

    # ── Results — rendered persistently from session state ────────────────
    # This block runs on every rerun so widgets inside (comparison checkbox,
    # shortlist button, leaderboard expanders, etc.) stay visible after any
    # user interaction.
    if st.session_state.last_results:
        results = st.session_state.last_results
        last_job = st.session_state.last_job or selected_jobs[0]

        # Stats
        avg_time = st.session_state.total_ranking_time / max(st.session_state.ranking_runs, 1)
        stats_c1, stats_c2 = st.columns(2)
        stats_c1.metric("Total candidates processed", st.session_state.total_candidates_processed)
        stats_c2.metric("Average ranking time", f"{avg_time:.2f}s")

        # CSV export
        df_export = pd.DataFrame(results)[
            ["id", "name", "role", "final_score", "semantic_score", "momentum_score"]
        ]
        csv = df_export.to_csv(index=False)
        st.download_button(
            "📥 Download Ranked CSV",
            csv,
            file_name="ranked_candidates.csv",
            mime="text/csv",
        )

        # Multi-job matrix view
        if len(selected_jobs) > 1 and st.session_state.get("all_job_results"):
            st.subheader("🔀 Multi-Job Ranking Matrix")
            matrix_rows: list[dict[str, Any]] = []
            all_jr = st.session_state.all_job_results
            candidate_names = {r["name"] for res in all_jr.values() for r in res}
            for name in sorted(candidate_names):
                row: dict[str, Any] = {"Candidate": name}
                for job_title, job_res in all_jr.items():
                    match = next((r for r in job_res if r["name"] == name), None)
                    row[job_title] = match["final_score"] if match else 0.0
                matrix_rows.append(row)
            df_matrix = pd.DataFrame(matrix_rows).set_index("Candidate")
            st.dataframe(
                df_matrix.style.background_gradient(cmap="YlGn", axis=None),
                use_container_width=True,
            )

        # Comparison
        render_comparison(results, last_job["description"], api_key=api_key)

        # Shortlist
        render_shortlist(get_available_roles())

        # Analytics
        render_analytics(results)

        # Leaderboard
        render_leaderboard(results, last_job["description"], api_key=api_key)

    # ── History ──────────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("🕓 Ranking History"):
        snapshots = list_snapshots()
        if snapshots:
            selected_snap = st.selectbox("Select snapshot", snapshots)
            if st.button("Load Snapshot"):
                snap = load_snapshot(selected_snap)

                st.markdown(f"### Snapshot: {snap.get('job_title', 'Unknown Job')}")

                c1, c2 = st.columns(2)

                raw_ts = snap.get("timestamp", "")
                display_ts = "N/A"
                if raw_ts:
                    try:
                        dt = datetime.strptime(raw_ts, "%Y%m%dT%H%M%SZ")
                        display_ts = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except ValueError:
                        display_ts = raw_ts

                c1.metric("Date/Time", display_ts)
                c2.metric("Candidates Ranked", snap.get("candidate_count", 0))

                with st.expander("⚙️ Weights Used"):
                    wc1, wc2 = st.columns(2)
                    with wc1:
                        st.markdown("**Main Weights**")
                        st.json(snap.get("weights", {}))
                    with wc2:
                        st.markdown("**Momentum Config**")
                        st.json(snap.get("momentum_config", {}))

                if "results" in snap and snap["results"]:
                    df_snap = pd.DataFrame(snap["results"])[
                        ["id", "name", "role", "final_score", "semantic_score", "momentum_score"]
                    ]
                    st.dataframe(df_snap, use_container_width=True)
                else:
                    st.info("No candidate results found in this snapshot.")
        else:
            st.info("No ranking history yet. Run a ranking to create a snapshot.")

    # ── Raw Data Table with Deletion ─────────────────────────────────────
    with st.expander("📋 View Raw Candidate Data"):
        if st.session_state.candidates:
            df = pd.DataFrame(st.session_state.candidates)
            st.dataframe(df)

            # Deletion by name
            del_name = st.selectbox(
                "Select candidate to remove",
                ["(none)"] + [c.get("name", "?") for c in st.session_state.candidates],
                key="delete_candidate_select",
            )
            if del_name != "(none)" and st.button(f"🗑️ Remove {del_name}"):
                st.session_state.candidates = [
                    c for c in st.session_state.candidates if c.get("name") != del_name
                ]
                st.success(f"Removed {del_name}.")
                st.rerun()
