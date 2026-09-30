
import streamlit as st
import pandas as pd
from agent import evaluate_proposal, add_ppi, extract_pdf_text, save_results, CRITERIA

st.set_page_config(page_title="RFP Evaluation Agent", page_icon="📊", layout="wide")
st.title("📊 RFP Evaluation Agent")
st.caption("AI-assisted proposal evaluation using weighted criteria, peer benchmarking and SQLite persistence.")

with st.sidebar:
    st.header("Evaluation Rubric")
    for name, cfg in CRITERIA.items():
        st.write(f"**{name}** — {cfg['weight']*100:.0f}%")
    st.divider()
    st.info("Optional LLM mode: set OPENAI_API_KEY. Without a key, the app uses a deterministic rubric fallback so the demo remains runnable.")

files = st.file_uploader("Upload 2–5 proposal PDFs", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 Evaluate Proposals", type="primary"):
        results = []
        progress = st.progress(0)
        for i, f in enumerate(files):
            text = extract_pdf_text(f.read())
            results.append(evaluate_proposal(f.name, text))
            progress.progress((i + 1) / len(files))

        results = add_ppi(results)
        save_results(results)

        st.session_state["results"] = results
        st.success(f"Evaluated {len(results)} proposals and stored results in SQLite.")

if "results" in st.session_state:
    results = st.session_state["results"]

    st.subheader("🏆 Evaluation Summary")
    rows = []
    for r in results:
        rows.append({
            "Rank": r["rank"],
            "Proposal": r["proposal"],
            "Absolute Score": r["absolute_score"],
            "PPI": r["ppi"],
            "Method": r["method"]
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("📈 Criterion Scores")
    score_rows = []
    for r in results:
        row = {"Proposal": r["proposal"]}
        row.update({k: round(v, 2) for k, v in r["scores"].items()})
        score_rows.append(row)
    st.dataframe(pd.DataFrame(score_rows).set_index("Proposal"), use_container_width=True)

    st.subheader("🔎 Detailed Rationale")
    for r in results:
        with st.expander(f"Rank #{r['rank']} — {r['proposal']}"):
            st.write(f"**Absolute score:** {r['absolute_score']}/100")
            st.write(f"**Peer Performance Index:** {r['ppi']}%")
            st.write(f"**Evaluation method:** {r['method']}")
            st.write("**Rationale:**", r["rationale"])
            if r["strengths"]:
                st.write("**Strengths:**")
                for x in r["strengths"]:
                    st.write(f"- {x}")
            if r["risks"]:
                st.write("**Risks / gaps:**")
                for x in r["risks"]:
                    st.write(f"- {x}")

    st.download_button(
        "Download results as JSON",
        data=pd.DataFrame(rows).to_json(orient="records", indent=2),
        file_name="rfp_evaluation_results.json",
        mime="application/json"
    )
else:
    st.markdown("""
### How it works
1. Upload multiple RFP proposal PDFs.
2. Extract proposal text.
3. Score each proposal against five weighted criteria.
4. Calculate an absolute weighted score out of 100.
5. Calculate PPI relative to the best proposal.
6. Rank proposals deterministically.
7. Persist evaluation records to SQLite.
""")
