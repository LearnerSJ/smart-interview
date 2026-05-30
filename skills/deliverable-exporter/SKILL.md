---
name: deliverable-exporter
description: Export the study into an Excel report, Word PRD, or Markdown brief. Runs only after qa-validator passes.
---

# deliverable-exporter (v0.2)

## Inputs
`study_db` (must have passed QA), `format` in {excel, word, md, all}.

## Contract
- Read from the study ledger via `scripts/study.py` — never re-derive content from chat
  state. The SQLite study is the source of truth; all deliverables are regenerable views.
- STRONG-and-confident assumptions feed MVP/PRD scope; CONTESTED feed Open Questions;
  every claim traces back to interview quotes (evidence appendix).
- Do not include WEAK or INVALIDATED content in the body (appendix only).

## How to run

```bash
# Excel report (6 views: Dashboard, Evidence Ledger, Assumption x Interview, Interviews,
# Use Case Priority, PRD Feed)
python3 scripts/study.py export --db "$STUDY_DB" --out output/<slug>.xlsx

# PRD — Word and/or Markdown
python3 scripts/study.py export-prd --db "$STUDY_DB" --format word|md|all
```

Outputs land under `output/`:
- `<slug>.xlsx`      — the 6-view Excel report
- `<slug>_PRD.docx`  — Word PRD (problem, method, validated scope, open questions, prioritisation, evidence appendix)
- `<slug>_PRD.md`    — same content as Markdown

## Final response
Return the list of generated paths to the orchestrator for the end-of-run summary.
