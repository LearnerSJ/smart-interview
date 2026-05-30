#!/usr/bin/env python3
"""PRD generation (v0.2): Word + Markdown, built from the ledger.

A PRD is a synthesis VIEW of the study, not a new source of data. Structure:
  1. Problem & hypothesis (intake)
  2. Method (n interviews, segments, consent posture)
  3. Validated scope  — STRONG-and-confident assumptions only
  4. Open questions    — CONTESTED assumptions
  5. Prioritisation    — weighted use-case ranking
  6. Evidence appendix — every requirement traces to interview quotes

Each scope item carries its supporting quotes, so any reader can go
requirement -> assumption -> exact client quote.
"""
from __future__ import annotations
from pathlib import Path


def _evidence_for(aid, signals):
    return [s for s in signals if s["assumption_id"] == aid]


def build_markdown(study, scores, assumptions, interviews, signals, ranked, sat):
    L = []
    L.append(f"# {study['name']} — PRD\n")
    intake = study.get("intake", {})
    L.append("## 1. Problem & Hypothesis\n")
    for k in ("problem_statement", "target_user", "hypothesis", "success_metric"):
        if intake.get(k):
            L.append(f"- **{k.replace('_',' ').title()}:** {intake[k]}")
    L.append(f"\n## 2. Method\n\n{len(interviews)} interview(s). {sat['verdict']}")
    consented = sum(1 for iv in interviews if iv.get("consent"))
    L.append(f"Consent on record: {consented}/{len(interviews)}.\n")

    L.append("## 3. Validated Scope (STRONG only)\n")
    strong = [a for a in assumptions if scores[a["id"]]["class"] == "STRONG"]
    if not strong:
        L.append("_No assumption has reached STRONG with adequate confidence yet._")
    for a in strong:
        v = scores[a["id"]]
        L.append(f"\n### {a['id']} — {a['text']}")
        L.append(f"_{v['why']}_\n")
        for s in _evidence_for(a["id"], signals):
            if s["score"] > 0 and s.get("quote"):
                L.append(f"  - ({s['score']:+}) [{s['interview_id']} {s.get('line_ref') or ''}] \"{s['quote']}\"")

    L.append("\n## 4. Open Questions (CONTESTED)\n")
    contested = [a for a in assumptions if scores[a["id"]]["class"] == "CONTESTED"]
    if not contested:
        L.append("_None._")
    for a in contested:
        v = scores[a["id"]]
        L.append(f"- **{a['id']}** {a['text']} — {v['why']}")

    L.append("\n## 5. Prioritisation (weighted)\n")
    if ranked:
        L.append("| Use Case | Score | Priority | Linked |")
        L.append("|---|---|---|---|")
        for u in ranked:
            L.append(f"| {u['name']} | {u['weighted_score']} | {u['priority']} | {u.get('linked_assumptions') or ''} |")
    else:
        L.append("_No use cases scored yet._")

    L.append("\n## 6. Evidence Appendix\n")
    L.append("| signal | interview | assumption | score | quote |")
    L.append("|---|---|---|---|---|")
    for s in signals:
        q = (s.get("quote") or "").replace("|", "/")
        L.append(f"| {s['id']} | {s['interview_id']} | {s['assumption_id']} | {s['score']:+} | {q} |")
    return "\n".join(L) + "\n"


def build_word(path, study, scores, assumptions, interviews, signals, ranked, sat):
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.add_heading(f"{study['name']} — PRD", level=0)

    doc.add_heading("1. Problem & Hypothesis", level=1)
    intake = study.get("intake", {})
    for k in ("problem_statement", "target_user", "hypothesis", "success_metric"):
        if intake.get(k):
            p = doc.add_paragraph()
            p.add_run(f"{k.replace('_',' ').title()}: ").bold = True
            p.add_run(intake[k])

    doc.add_heading("2. Method", level=1)
    consented = sum(1 for iv in interviews if iv.get("consent"))
    doc.add_paragraph(f"{len(interviews)} interview(s). {sat['verdict']} "
                      f"Consent on record: {consented}/{len(interviews)}.")

    doc.add_heading("3. Validated Scope (STRONG only)", level=1)
    strong = [a for a in assumptions if scores[a["id"]]["class"] == "STRONG"]
    if not strong:
        doc.add_paragraph("No assumption has reached STRONG with adequate confidence yet.")
    for a in strong:
        v = scores[a["id"]]
        doc.add_heading(f"{a['id']} — {a['text']}", level=2)
        ip = doc.add_paragraph(); ip.add_run(v["why"]).italic = True
        for s in _evidence_for(a["id"], signals):
            if s["score"] > 0 and s.get("quote"):
                doc.add_paragraph(
                    f"({s['score']:+}) [{s['interview_id']} {s.get('line_ref') or ''}] “{s['quote']}”",
                    style="List Bullet")

    doc.add_heading("4. Open Questions (CONTESTED)", level=1)
    contested = [a for a in assumptions if scores[a["id"]]["class"] == "CONTESTED"]
    if not contested:
        doc.add_paragraph("None.")
    for a in contested:
        doc.add_paragraph(f"{a['id']} {a['text']} — {scores[a['id']]['why']}", style="List Bullet")

    doc.add_heading("5. Prioritisation (weighted)", level=1)
    if ranked:
        t = doc.add_table(rows=1, cols=4); t.style = "Light Grid Accent 1"
        for i, h in enumerate(("Use Case", "Score", "Priority", "Linked")):
            t.rows[0].cells[i].text = h
        for u in ranked:
            c = t.add_row().cells
            c[0].text = u["name"]; c[1].text = str(u["weighted_score"])
            c[2].text = u["priority"]; c[3].text = u.get("linked_assumptions") or ""
    else:
        doc.add_paragraph("No use cases scored yet.")

    doc.add_heading("6. Evidence Appendix", level=1)
    t = doc.add_table(rows=1, cols=5); t.style = "Light Grid Accent 1"
    for i, h in enumerate(("Signal", "Interview", "Assumption", "Score", "Quote")):
        t.rows[0].cells[i].text = h
    for s in signals:
        c = t.add_row().cells
        c[0].text = str(s["id"]); c[1].text = s["interview_id"]
        c[2].text = s["assumption_id"]; c[3].text = f"{s['score']:+}"
        c[4].text = s.get("quote") or ""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    return path
