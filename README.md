# RFP Evaluation Agent

## Objective
Evaluate multiple RFP proposals against a fixed weighted rubric, calculate absolute scores and Peer Performance Index (PPI), rank proposals, generate rationale, and persist evaluation records in SQLite.

## Rubric
| Criterion | Weight |
|---|---:|
| Technical Capability | 25% |
| Implementation Plan | 20% |
| Commercial Value | 20% |
| Security & Compliance | 20% |
| Support & Experience | 15% |

## Architecture
- `app.py` — Streamlit UI
- `agent.py` — PDF extraction, evaluation, weighted scoring, PPI and persistence
- `database.py` — SQLite query helper
- `rfp_evaluation.db` — generated SQLite database
- `sample_proposals/` — synthetic proposal PDFs
- `RFP_Evaluation_Experiment.ipynb` — experimentation/prompt-engineering notebook

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Optional LLM mode
Set:
```bash
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
```

If no API key is available, the app automatically uses a deterministic rubric fallback so the demonstration remains runnable.

## PPI
PPI is calculated as:

`PPI = proposal absolute score / best proposal absolute score × 100`

This is a relative benchmark against the best submitted proposal.

## Submission
The LMS submission should contain the notebook and complete project folder. Put the GitHub and Streamlit URLs in the notebook's top cell.


### Streamlit Community Cloud Secrets

For Streamlit deployment, open **App → Settings → Secrets** and add:

```toml
OPENAI_API_KEY = "your-api-key"
OPENAI_MODEL = "gpt-4o-mini"
```

The application supports Streamlit Secrets for cloud deployment and environment variables for local development. Never commit your API key to GitHub.
