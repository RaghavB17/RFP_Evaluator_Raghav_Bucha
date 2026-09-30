
import os, json, re, sqlite3
from datetime import datetime
from pathlib import Path

CRITERIA = {
    "Technical Capability": {"weight": 0.25, "description": "Technical architecture, technology fit, scalability and delivery capability."},
    "Implementation Plan": {"weight": 0.20, "description": "Clarity, feasibility, milestones, resources, timeline and delivery methodology."},
    "Commercial Value": {"weight": 0.20, "description": "Cost transparency, value for money, pricing assumptions and commercial viability."},
    "Security & Compliance": {"weight": 0.20, "description": "Security controls, privacy, regulatory compliance, risk management and governance."},
    "Support & Experience": {"weight": 0.15, "description": "Relevant experience, SLA/support model, references and post-go-live support."},
}

def extract_pdf_text(file_bytes):
    """Extract text from a PDF. Uses pypdf when available."""
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        return f"PDF extraction error: {e}"

def _keyword_score(text, criterion):
    """Deterministic fallback scoring when no LLM API is configured."""
    t = text.lower()
    groups = {
        "Technical Capability": ["architecture", "api", "cloud", "scalable", "microservice", "database", "technology", "integration"],
        "Implementation Plan": ["milestone", "timeline", "implementation", "agile", "sprint", "delivery", "roadmap", "migration"],
        "Commercial Value": ["cost", "price", "budget", "license", "total cost", "roi", "commercial", "fixed fee"],
        "Security & Compliance": ["security", "encryption", "gdpr", "iso 27001", "compliance", "privacy", "iam", "audit", "backup"],
        "Support & Experience": ["sla", "support", "experience", "years", "client", "reference", "maintenance", "uptime", "helpdesk"],
    }
    hits = sum(1 for k in groups[criterion] if k in t)
    # Produce a useful 1-10 score without pretending this is an LLM judgment.
    return max(1, min(10, 3 + hits * 0.8))

def _openai_scores(text):
    """Optional LLM scoring. Requires OPENAI_API_KEY and the openai package."""
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    rubric = "\n".join(
        f"- {k} ({v['weight']*100:.0f}%): {v['description']}" for k,v in CRITERIA.items()
    )
    prompt = f"""You are an RFP evaluation analyst.
Evaluate the proposal against this fixed rubric.

{rubric}

Return ONLY valid JSON with:
{{
  "scores": {{
    "Technical Capability": 1-10,
    "Implementation Plan": 1-10,
    "Commercial Value": 1-10,
    "Security & Compliance": 1-10,
    "Support & Experience": 1-10
  }},
  "strengths": ["..."],
  "risks": ["..."],
  "rationale": "..."
}}

Be evidence-based and use only information present in the proposal.
Proposal:
{text[:30000]}"""
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type":"json_object"},
        messages=[{"role":"user","content":prompt}]
    )
    return json.loads(response.choices[0].message.content)

def evaluate_proposal(name, text):
    use_llm = bool(os.getenv("OPENAI_API_KEY"))
    if use_llm:
        try:
            result = _openai_scores(text)
            scores = {k: float(result["scores"][k]) for k in CRITERIA}
            rationale = result.get("rationale", "")
            strengths = result.get("strengths", [])
            risks = result.get("risks", [])
            method = "LLM rubric evaluation"
        except Exception as e:
            scores = {k: _keyword_score(text, k) for k in CRITERIA}
            rationale = f"Fallback deterministic evaluation used because LLM call failed: {e}"
            strengths, risks = [], []
            method = "Deterministic fallback"
    else:
        scores = {k: _keyword_score(text, k) for k in CRITERIA}
        rationale = "Deterministic rubric fallback used because no LLM API key was configured."
        strengths, risks = [], []
        method = "Deterministic fallback"

    weighted = sum(scores[k] * CRITERIA[k]["weight"] for k in CRITERIA)
    absolute_score = round(weighted * 10, 2)
    return {
        "proposal": name,
        "scores": scores,
        "absolute_score": absolute_score,
        "rationale": rationale,
        "strengths": strengths,
        "risks": risks,
        "method": method,
        "evaluated_at": datetime.utcnow().isoformat()
    }

def add_ppi(results):
    if not results:
        return results
    best = max(r["absolute_score"] for r in results) or 1
    for r in results:
        r["ppi"] = round((r["absolute_score"] / best) * 100, 2)
    # deterministic ordering: absolute score desc, then proposal name
    results.sort(key=lambda x: (-x["absolute_score"], x["proposal"]))
    for i, r in enumerate(results, 1):
        r["rank"] = i
    return results

def init_db(db_path="rfp_evaluation.db"):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proposal TEXT NOT NULL,
        technical REAL,
        implementation REAL,
        commercial REAL,
        security REAL,
        support_experience REAL,
        absolute_score REAL,
        ppi REAL,
        rank INTEGER,
        rationale TEXT,
        method TEXT,
        evaluated_at TEXT
    )""")
    con.commit()
    con.close()

def save_results(results, db_path="rfp_evaluation.db"):
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    for r in results:
        s = r["scores"]
        cur.execute("""INSERT INTO evaluations
        (proposal, technical, implementation, commercial, security, support_experience,
         absolute_score, ppi, rank, rationale, method, evaluated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (r["proposal"], s["Technical Capability"], s["Implementation Plan"],
         s["Commercial Value"], s["Security & Compliance"], s["Support & Experience"],
         r["absolute_score"], r["ppi"], r["rank"], r["rationale"], r["method"], r["evaluated_at"]))
    con.commit()
    con.close()
