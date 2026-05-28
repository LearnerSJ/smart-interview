---
name: qa-validator
description: Final gate. Verify workbook integrity, scoring consistency, and rule compliance before the workflow reports completion.
---

# qa-validator

## Checks (ALL must pass)

1. **Sheet set** — exactly: Guide, Assumption Matrix, Scoping Matrix, MVP Specifications, Evidence Log, Open Questions.
2. **Header lock** — headers match the canonical schema. Any drift -> FAIL.
3. **Coverage** — every assumption ID in `Assumption Matrix` also appears in `Evidence Log` (real signal or `no-signal`).
4. **MVP purity** — every `MVP Specifications` row links to an assumption classified STRONG. Any non-STRONG -> FAIL.
5. **Open Questions coverage** — every CONTESTED assumption appears in `Open Questions`.
6. **No leakage** — no WEAK / INVALIDATED assumption appears in MVP Specifications or Scoping Matrix.
7. **Evidence completeness** — every Assumption Matrix row's `evidence_refs` is non-empty.
8. **Spreadsheet safety** — no unescaped newlines in single-line columns; no markdown.

## How to run

```bash
python3 scripts/workbook.py qa --path "$WORKBOOK_PATH"
```

The script writes `pass` or `fail <reasons>` to `hooks/.qa_state`. The Stop hook reads that file and blocks completion until `pass`.

## Output

```json
{"pass": true, "failures": []}
```

On fail, return findings to the orchestrator. Do NOT mark workflow complete.
