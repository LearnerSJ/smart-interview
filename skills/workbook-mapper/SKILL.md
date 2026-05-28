---
name: workbook-mapper
description: Write scored assumptions and signals into the canonical Excel workbook sheets via scripts/workbook.py.
---

# workbook-mapper

## Inputs
`assumptions[]`, `signals[]`, `scores{}`, `workbook_path`.

## Sheet rules

### Assumption Matrix
One row per assumption. `score` = sum. `class` = STRONG/CONTESTED/WEAK/INVALIDATED. `evidence_refs` = comma-separated line_refs (or `no-signal`).

### MVP Specifications
ONE row per STRONG assumption, translated into a feature spec (`name`, `description`, `linked_assumptions`). WEAK/CONTESTED/INVALIDATED MUST NOT appear.

### Scoping Matrix
One row per use case grouped from STRONG assumptions. `priority` = P0 if backed by >=2 STRONG assumptions, else P1.

### Open Questions
One row per CONTESTED assumption. `reason` = brief note on the contradiction.

### Evidence Log
Append EVERY signal (including `no-signal` placeholders). Append-only.

## Write protocol

```bash
python3 scripts/workbook.py write \
  --path "$WORKBOOK_PATH" \
  --payload payload.json
```

`payload.json` has one key per sheet. The script:
- never modifies headers
- aborts if a write would change schema
- appends (not overwrites) Evidence Log

## Output
```json
{"sheets_written": [...], "rows_per_sheet": {...}}
```
