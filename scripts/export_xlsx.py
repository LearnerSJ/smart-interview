#!/usr/bin/env python3
"""Generate the Excel report from the study ledger (v0.2).

Excel is a VIEW, never the source of truth. Every sheet is regenerated from the
SQLite store on each export. Verdicts are written as computed VALUES (with a
plain-English "Why" column) — not live formulas — because the scoring model lives
in code (scoring.py). Six sheets:

  Dashboard            — per-assumption verdict + numbers + Why
  Evidence Ledger      — every signal with quote + line-ref (the audit trail)
  Assumption x Interview — generated wide pivot; cell comments carry the quote
  Interviews           — who/when/segment/ICP-fit/consent per call
  Use Case Priority    — weighted prioritisation matrix (code-fed)
  PRD Feed             — STRONG-and-confident assumptions -> requirement candidates
"""
from __future__ import annotations
from pathlib import Path
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Font, PatternFill, Alignment

HEADER_FILL = PatternFill("solid", fgColor="222222")
HEADER_FONT = Font(bold=True, color="FFFFFF")
CLASS_FILL = {
    "STRONG": PatternFill("solid", fgColor="E6F4EA"),
    "CONTESTED": PatternFill("solid", fgColor="FEF7E0"),
    "WEAK": PatternFill("solid", fgColor="F1F3F4"),
    "INVALIDATED": PatternFill("solid", fgColor="FCE8E6"),
}


def _header(ws, cols):
    ws.append(cols)
    for c in ws[1]:
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(vertical="center")


def build(path, study, assumptions, interviews, signals_all, scores, ranked=None):
    wb = Workbook()
    wb.remove(wb.active)

    # --- Dashboard -------------------------------------------------------
    ws = wb.create_sheet("Dashboard")
    _header(ws, ["#", "Cat.", "Assumption", "Class", "Strength", "Consensus",
                 "Confidence", "n", "Why"])
    for a in assumptions:
        sc = scores[a["id"]]
        ws.append([a["id"], a.get("category"), a["text"], sc["class"],
                   sc["strength"], sc["consensus"], sc["confidence"], sc["n"], sc["why"]])
        ws.cell(ws.max_row, 4).fill = CLASS_FILL.get(sc["class"], CLASS_FILL["WEAK"])
    ws.column_dimensions["C"].width = 50
    ws.column_dimensions["I"].width = 70

    # --- Evidence Ledger -------------------------------------------------
    ws = wb.create_sheet("Evidence Ledger")
    _header(ws, ["signal_id", "interview", "assumption", "score", "polarity",
                 "verified", "line_ref", "quote"])
    for s in signals_all:
        ws.append([s["id"], s["interview_id"], s["assumption_id"], s["score"],
                   s.get("polarity"), "yes" if s.get("verified") else "no",
                   s.get("line_ref"), s.get("quote")])
    ws.column_dimensions["H"].width = 80

    # --- Assumption x Interview (generated pivot) ------------------------
    ws = wb.create_sheet("Assumption x Interview")
    iv_ids = [iv["id"] for iv in interviews]
    _header(ws, ["#", "Assumption"] + iv_ids + ["Strength", "Class"])
    # index signals by (assumption, interview) -> averaged score + quotes
    cell_idx = {}
    for s in signals_all:
        cell_idx.setdefault((s["assumption_id"], s["interview_id"]), []).append(s)
    for a in assumptions:
        sc = scores[a["id"]]
        row = [a["id"], a["text"]]
        for iv in iv_ids:
            sigs = cell_idx.get((a["id"], iv))
            row.append(round(sum(x["score"] for x in sigs) / len(sigs), 2) if sigs else None)
        row += [sc["strength"], sc["class"]]
        ws.append(row)
        # attach quotes as cell comments
        for j, iv in enumerate(iv_ids):
            sigs = cell_idx.get((a["id"], iv))
            if sigs:
                q = " | ".join(f"({x['score']:+}) {x.get('quote') or ''}".strip() for x in sigs)
                ws.cell(ws.max_row, 3 + j).comment = Comment(q[:1000], "scoring")
    ws.column_dimensions["B"].width = 50

    # --- Interviews ------------------------------------------------------
    ws = wb.create_sheet("Interviews")
    _header(ws, ["id", "seq", "label", "date", "role", "firm", "segment",
                 "icp_fit", "consent", "source", "transcript_ref"])
    for iv in interviews:
        ws.append([iv["id"], iv["seq"], iv.get("label"), iv.get("date"),
                   iv.get("interviewee_role"), iv.get("firm"), iv.get("segment"),
                   iv.get("icp_fit"), "yes" if iv.get("consent") else "NO",
                   iv.get("source"), iv.get("transcript_ref")])

    # --- Use Case Priority (code-fed at synthesis) -----------------------
    ws = wb.create_sheet("Use Case Priority")
    _header(ws, ["#", "Use Case", "Description", "Customer Value (35%)",
                 "Strategic Fit (25%)", "Feasibility (25%)", "Time to Value (15%)",
                 "Weighted Score", "Priority", "Linked"])
    for i, u in enumerate(ranked or [], 1):
        ws.append([i, u["name"], u.get("description"), u.get("customer_value"),
                   u.get("strategic_fit"), u.get("feasibility"), u.get("time_to_value"),
                   u.get("weighted_score"), u.get("priority"), u.get("linked_assumptions")])
    ws.column_dimensions["B"].width = 36
    ws.column_dimensions["C"].width = 46

    # --- PRD Feed --------------------------------------------------------
    ws = wb.create_sheet("PRD Feed")
    _header(ws, ["assumption", "text", "class", "strength", "confidence",
                 "evidence_signal_ids", "Why"])
    for a in assumptions:
        sc = scores[a["id"]]
        if sc["class"] == "STRONG":
            ev = ",".join(str(s["id"]) for s in signals_all if s["assumption_id"] == a["id"])
            ws.append([a["id"], a["text"], sc["class"], sc["strength"],
                       sc["confidence"], ev, sc["why"]])
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["G"].width = 70

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
