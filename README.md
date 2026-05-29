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

## Ranking & Scoring Logic

This section outlines the details of how the ranking pipeline filters, scores, and explains candidate recommendations.

### 1. Pre-Ranking Filter
Before candidate scoring begins, candidates can be filtered using `core.filters.filter_candidates` based on a series of criteria:
*   **Role & Location**: Case-insensitive substring matching on candidate's current role and geographic location.
*   **Resume Keyword**: Case-insensitive substring matching within the raw resume text.
*   **GitHub Commits (90d)**: Minimum threshold of commits.
*   **Certifications (1y)**: Minimum threshold of certifications.
*   **New Skills (180d)**: Minimum threshold of new skills acquired.

Only candidates who pass **all** applied filters are passed to the ranking pipeline.

---

### 2. Scoring Components

The final ranking is determined by a weighted blend of two main scores: the **Semantic Score** and the **Momentum Score**.

#### A. Semantic Score (Job Fit)
*   **Embedding Model**: Uses the `all-MiniLM-L6-v2` SentenceTransformer model (locally cached and lazy-loaded).
*   **Calculation**:
    1.  Encodes the selected Job Description and candidate resumes into vector embeddings.
    2.  Computes the **Cosine Similarity** between the Job Description embedding and each candidate resume embedding.
*   **Formula**:
    $$\text{Semantic Score} = \text{CosineSimilarity}(\vec{E}_{\text{job}}, \vec{E}_{\text{resume}})$$

#### B. Momentum Score (Activity & Stability)
The Momentum Score measures the candidate's recent professional activity and job-transition pattern. It aggregates 5 normalized behavioural signals (each capped at $1.0$):

1.  **GitHub Commits**: Normalized to 100 commits over the last 90 days.
    $$\text{GitHub Score} = \min\left(\frac{\text{Commits}_{90d}}{100}, 1.0\right)$$
2.  **LinkedIn Posts**: Normalized to 20 posts over the last 30 days.
    $$\text{LinkedIn Score} = \min\left(\frac{\text{Posts}_{30d}}{20}, 1.0\right)$$
3.  **Certifications**: Normalized to 5 certifications earned in the last year.
    $$\text{Cert Score} = \min\left(\frac{\text{Certs}_{1y}}{5}, 1.0\right)$$
4.  **Growth Velocity**: Normalized to 10 skills acquired in the last 180 days.
    $$\text{Growth Score} = \min\left(\frac{\text{Skills}_{180d}}{10}, 1.0\right)$$
5.  **Stability / Job-Change Signal**: Calculated using the number of job changes in the last 2 years:
    *   **1 to 2 changes**: Active candidate ($1.0$)
    *   **0 changes**: Stable candidate ($0.5$)
    *   **More than 2 changes**: High job-hopping risk ($0.3$)

##### Composite Weighted Score & Recency Bonus
*   **Weighted Sum**: The 5 sub-scores are combined using user-configurable momentum sub-weights (which default to $0.2$ each):
    $$\text{Base Momentum} = \sum (\text{Signal Score} \times \text{Signal Weight})$$
*   **Recency Bonus**: Multiplicative bonus for highly active candidates:
    *   $+0.05$ if LinkedIn posts in the last 30 days $> 10$
    *   $+0.05$ if GitHub commits in the last 90 days $> 50$
    *   $\text{Recency Bonus Factor} = 1.0 + \text{earned bonuses}$ (up to $1.10$)
*   **Final Momentum**:
    $$\text{Momentum Score} = \min(\text{Base Momentum} \times \text{Recency Bonus Factor}, 1.0)$$ (rounded to 2 decimal places)

---

### 3. Final Scoring and Ranking

The overall **Final Score** is a weighted blend of the Semantic Score and the Momentum Score (rounded to 3 decimal places):

$$\text{Final Score} = \left(\text{Semantic Score} \times W_{\text{semantic}}\right) + \left(\text{Momentum Score} \times W_{\text{momentum}}\right)$$

*   **Default Weights**: $W_{\text{semantic}} = 0.7$ and $W_{\text{momentum}} = 0.3$.
*   **Sorting**: The candidate list is sorted in descending order of their **Final Score**.

---

### 4. Ranking Explanations

Each ranked candidate is paired with a natural-language explanation of their fit:
1.  **LLM-Powered Explanations (Groq)**:
    *   If a Groq API key is provided, the app prompts `llama-3.3-70b-versatile` with the job description, candidate scores, and profile.
    *   It requests a concise, one-sentence summary (max 25 words).
2.  **Rule-Based Fallback**:
    *   If the API key is missing or fails (e.g. invalid key or network issue), a deterministic heuristic is used:
        *   Semantic Score $> 0.7$ $\rightarrow$ *"strong semantic alignment"*
        *   $0.5 <$ Semantic Score $\le 0.7$ $\rightarrow$ *"moderate semantic alignment"*
        *   Momentum Score $> 0.5$ $\rightarrow$ *"strong recent momentum"*
        *   $0.3 <$ Momentum Score $\le 0.5$ $\rightarrow$ *"moderate recent momentum"*
        *   Constructs: `"[Candidate Name] is a strong fit because [Semantic reason] and [Momentum reason]."`

