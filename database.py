
import sqlite3

DB_PATH = "rfp_evaluation.db"

def query_evaluations():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""
        SELECT proposal, technical, implementation, commercial, security,
               support_experience, absolute_score, ppi, rank, evaluated_at
        FROM evaluations
        ORDER BY rank
    """).fetchall()
    con.close()
    return rows
