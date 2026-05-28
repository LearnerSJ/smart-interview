---
name: deliverable-exporter
description: Export the populated workbook into a Word PRD, PowerPoint readout, or Markdown brief. Runs only after qa-validator passes.
---

# deliverable-exporter

## Inputs
`workbook_path` (must have passed QA), `format` in {word, ppt, md, all}.

## Contract
- Read the workbook — never re-derive content from chat state. The workbook is the source of truth.
- Use STRONG assumptions for MVP sections, CONTESTED for Open Questions, all signals for Evidence.
- Do not include WEAK or INVALIDATED content in the body of deliverables (footnote only if asked).

## How to run

```bash
python3 scripts/exporters.py \
  --path "$WORKBOOK_PATH" \
  --format word|ppt|md|all \
  --out output/
```

Outputs land alongside the workbook:
- `<slug>.docx` — PRD (problem, hypothesis, MVP scope, open questions, evidence appendix)
- `<slug>.pptx` — readout deck (8-10 slides)
- `<slug>.md`   — Markdown brief (same content as PRD, plain text)

## Final response
Return the list of generated paths to the orchestrator. The orchestrator surfaces them in the end-of-run summary.
