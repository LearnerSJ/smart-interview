---
name: qa-validator
description: Final gate (v0.2). Verify study integrity — consent, evidence provenance, and STRONG-is-evidenced — before the workflow reports completion.
---

# qa-validator (v0.2)

Validates the study ledger (the source of truth), not a spreadsheet. The verdict is
computed in code, so QA checks the *inputs* and *integrity*, not hand-scored cells.

## Checks

**Fail (block completion):**
1. **Consent** — every interview has consent on record (financial-services / EU requirement).
2. **Provenance** — every signal has a verbatim `quote` and a `line_ref`.
3. **STRONG-is-evidenced** — every STRONG assumption has at least one positive signal.

**Warn (non-blocking):**
- **Thin coverage** — assumptions still at `n<=2` (low confidence); surfaced as a saturation hint.

## How to run

```bash
python3 scripts/study.py qa --db "$STUDY_DB"
```

The script writes `pass` or `fail <reasons>` to `hooks/.qa_state`. The Stop hook reads
that file and blocks completion until `pass`.

## Output

```json
{"pass": true, "failures": [], "warnings": ["thin (n<=2): A3, A6"]}
```

On fail, return findings to the orchestrator. Do NOT mark the workflow complete.
