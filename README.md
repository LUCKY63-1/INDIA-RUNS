# AI Recruiter POC

AI Recruiter POC is a recruiting demo that can run as either a Streamlit app or a customtkinter desktop app. It ranks and shortlists candidates using a blend of semantic matching, momentum signals, and explainable outputs.

## Current Features

1. **Semantic + Momentum Ranking**
    - Uses embedding similarity for job-fit and combines it with momentum signals (GitHub, LinkedIn, certifications, growth, stability).

2. **Interactive Weight Controls**
    - Live sliders for main weights and momentum sub-weights.
    - Preset buttons: Balanced, Aggressive Hiring, Quality Focus.
    - Reset to default controls.

3. **Candidate Filtering Before Ranking**
    - Filter by role text, resume keyword, minimum commits, certifications, new skills, and optional location.

4. **Explainability**
    - Short, consistent ranking explanations.
    - Groq-powered explanation path with rule-based fallback.
    - "How scoring works" section in the UI.

5. **Recruiter Workflow Features**
    - Compare top candidates side-by-side.
    - Role-based shortlist creation (Top N).
    - Ranked CSV and shortlist CSV download.
    - Ranking analytics and weak-signal visibility.

6. **History and Snapshots**
    - Stores ranking snapshots and allows loading previous runs from history.

7. **Data Management**
    - Load preset datasets from the data folder.
    - Upload CSV/JSON datasets.
    - Add candidates manually and persist to active preset file.

## Project Structure

- `app.py`: Main Streamlit orchestrator.
- `config/`
  - `weights.py`: Default weight constants and keys.
- `core/`
  - `ranking.py`: Ranking pipeline.
  - `momentum.py`: Momentum score logic.
  - `explanation.py`: LLM/fallback explanation generation.
  - `filters.py`: Candidate filtering utilities.
  - `skills.py`: Skill extraction/analysis helpers.
  - `history.py`: Snapshot save/load/list utilities.
- `ui/`
  - `sidebar.py`: Sidebar controls and context assembly.
  - `leaderboard.py`: Main results rendering.
  - `comparison.py`: Side-by-side comparison views.
  - `shortlist.py`: Role-based shortlist UI.
  - `analytics.py`: Metrics and analytics panels.
  - `empty_state.py`: Empty-state guidance.
- `data/`
  - Candidate and job JSON files.
  - `history/`: Ranking snapshots.
  - `loader.py`: Data loading helper.
- `utils/embeddings.py`: Embedding model utilities.
- `tests/`: Automated tests.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Desktop App

Run the customtkinter version with:

```bash
python desktop_app.py
```

This version keeps the same ranking backend but feels more like a traditional desktop application with panels, tabs, tables, and async ranking updates.

## Optional Environment Variables

- `HF_TOKEN`: Improves Hugging Face download limits and reliability.

You can place `HF_TOKEN` in `.env` (already supported via `python-dotenv`) or set it in your shell.
The Groq API key is entered directly in the app sidebar, so it is not required in `.env`.

## API Key Handling

- The Groq API key is requested from the user in the Streamlit sidebar.
- If the key is left empty, the app automatically uses the fallback explanation.
- If the key is invalid, the app also falls back instead of surfacing an error to the user.

## Scoring Overview

1. **Semantic Score**
    - Encodes the selected job description and candidate resume text, then computes similarity.

2. **Momentum Score**
    - Aggregates behavioral signals:
      - GitHub commits (90d)
      - LinkedIn posts (30d)
      - Certifications (1y)
      - Skills acquired (180d)
      - Stability/movement proxy

3. **Final Score**
    - Weighted blend of semantic and momentum scores, then sorted descending for leaderboard and shortlist.
