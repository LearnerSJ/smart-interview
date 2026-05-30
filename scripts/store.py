#!/usr/bin/env python3
"""Local study store for the Smart Interview workflow (v0.2, single-PM).

SQLite is the SOURCE OF TRUTH. Excel / Word / PPT are regenerable views built
from this store — they never own data. One study per database file.

Tables:
  study       — single row: identity + intake + scoring config (JSON blobs)
  assumptions — testable claims; emergent ones carry the interview they appeared in
  interviews  — one row per client call, with metadata used for weighting/consent
  signals     — the tidy evidence ledger: one row per (interview x assumption) signal
"""
from __future__ import annotations
import json, sqlite3, datetime
from pathlib import Path

SCORE_SET = {-1.0, 0.0, 0.5, 1.0}  # -1 No, 0 Unclear, +0.5 Partial, +1 Yes

DEFAULT_SCORING = {
    "strong_strength_min": 0.5,        # weighted-mean stance to qualify as STRONG
    "invalidated_strength_max": -0.34, # weighted-mean at/below this => INVALIDATED
    "contested_minority_share": 0.30,  # both camps >= this (weighted) => CONTESTED
    "confidence_low_max_n": 2,         # n <= this => low confidence
    "confidence_medium_max_n": 4,      # n <= this => medium; else high
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS study (
  id            INTEGER PRIMARY KEY CHECK (id = 1),
  name          TEXT NOT NULL,
  slug          TEXT NOT NULL,
  created_at    TEXT NOT NULL,
  intake        TEXT NOT NULL DEFAULT '{}',
  scoring_config TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS assumptions (
  id                  TEXT PRIMARY KEY,
  text                TEXT NOT NULL,
  category            TEXT,
  priority            TEXT,
  status              TEXT NOT NULL DEFAULT 'active',
  created_at_interview TEXT
);
CREATE TABLE IF NOT EXISTS interviews (
  id              TEXT PRIMARY KEY,
  label           TEXT,
  date            TEXT,
  interviewee_role TEXT,
  firm            TEXT,
  segment         TEXT,
  icp_fit         REAL NOT NULL DEFAULT 1.0,
  consent         INTEGER NOT NULL DEFAULT 0,
  source          TEXT,
  transcript_ref  TEXT,
  added_at        TEXT NOT NULL,
  seq             INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS signals (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  interview_id  TEXT NOT NULL REFERENCES interviews(id),
  assumption_id TEXT NOT NULL REFERENCES assumptions(id),
  score         REAL NOT NULL,
  polarity      TEXT,
  quote         TEXT,
  line_ref      TEXT,
  verified      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS use_cases (
  id              TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  description     TEXT,
  customer_value  REAL,
  strategic_fit   REAL,
  feasibility     REAL,
  time_to_value   REAL,
  linked_assumptions TEXT
);
"""


def _now() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def connect(db_path: str | Path) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def study_exists(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT 1 FROM study WHERE id = 1").fetchone() is not None


def create_study(conn, name, slug, intake=None, assumptions=None, scoring_config=None):
    if study_exists(conn):
        raise ValueError("study already exists in this database (use --force to recreate)")
    cfg = {**DEFAULT_SCORING, **(scoring_config or {})}
    conn.execute(
        "INSERT INTO study (id, name, slug, created_at, intake, scoring_config) VALUES (1,?,?,?,?,?)",
        (name, slug, _now(), json.dumps(intake or {}), json.dumps(cfg)),
    )
    for a in (assumptions or []):
        add_assumption(conn, a["id"], a["text"], a.get("category"), a.get("priority"),
                       created_at_interview=None)
    conn.commit()


def add_assumption(conn, aid, text, category=None, priority=None, created_at_interview=None):
    conn.execute(
        "INSERT OR REPLACE INTO assumptions (id, text, category, priority, status, created_at_interview) "
        "VALUES (?,?,?,?, COALESCE((SELECT status FROM assumptions WHERE id=?), 'active'), ?)",
        (aid, text, category, priority, aid, created_at_interview),
    )
    conn.commit()


def add_interview(conn, interview: dict, signals: list[dict]) -> dict:
    iid = interview["id"]
    if conn.execute("SELECT 1 FROM interviews WHERE id=?", (iid,)).fetchone():
        raise ValueError(f"interview '{iid}' already recorded (ledger is append-only; pick a new id)")
    seq = (conn.execute("SELECT COALESCE(MAX(seq),0) FROM interviews").fetchone()[0]) + 1
    conn.execute(
        "INSERT INTO interviews (id,label,date,interviewee_role,firm,segment,icp_fit,consent,source,transcript_ref,added_at,seq) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (iid, interview.get("label"), interview.get("date"), interview.get("interviewee_role"),
         interview.get("firm"), interview.get("segment"), float(interview.get("icp_fit", 1.0)),
         1 if interview.get("consent") else 0, interview.get("source"),
         interview.get("transcript_ref"), _now(), seq),
    )
    known = {r["id"] for r in conn.execute("SELECT id FROM assumptions")}
    written = 0
    for s in signals:
        if s["assumption_id"] not in known:
            raise ValueError(f"signal references unknown assumption '{s['assumption_id']}'")
        score = float(s["score"])
        if score not in SCORE_SET:
            raise ValueError(f"score {score} not in {sorted(SCORE_SET)}")
        conn.execute(
            "INSERT INTO signals (interview_id,assumption_id,score,polarity,quote,line_ref,verified) "
            "VALUES (?,?,?,?,?,?,?)",
            (iid, s["assumption_id"], score, s.get("polarity"), s.get("quote"),
             s.get("line_ref"), 1 if s.get("verified") else 0),
        )
        written += 1
    conn.commit()
    return {"interview": iid, "seq": seq, "signals_written": written}


# ---- read helpers ---------------------------------------------------------

def get_study(conn) -> dict:
    r = conn.execute("SELECT * FROM study WHERE id=1").fetchone()
    if not r:
        raise ValueError("no study in this database")
    d = dict(r)
    d["intake"] = json.loads(d["intake"])
    d["scoring_config"] = json.loads(d["scoring_config"])
    return d


def list_assumptions(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM assumptions ORDER BY id")]


def list_interviews(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM interviews ORDER BY seq")]


def list_signals(conn, assumption_id=None) -> list[dict]:
    if assumption_id:
        rows = conn.execute("SELECT * FROM signals WHERE assumption_id=? ORDER BY id", (assumption_id,))
    else:
        rows = conn.execute("SELECT * FROM signals ORDER BY id")
    return [dict(r) for r in rows]


def set_use_cases(conn, use_cases: list[dict]):
    """Replace the use-case set (PM-supplied dimension scores)."""
    conn.execute("DELETE FROM use_cases")
    for u in use_cases:
        conn.execute(
            "INSERT INTO use_cases (id,name,description,customer_value,strategic_fit,"
            "feasibility,time_to_value,linked_assumptions) VALUES (?,?,?,?,?,?,?,?)",
            (u["id"], u["name"], u.get("description"), u.get("customer_value"),
             u.get("strategic_fit"), u.get("feasibility"), u.get("time_to_value"),
             ",".join(u.get("linked_assumptions", []))),
        )
    conn.commit()


def list_use_cases(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM use_cases ORDER BY id")]
