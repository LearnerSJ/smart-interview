# Smart Interview — Global Rules

These rules apply to every skill, tool call, and output in this workflow.

## Workbook integrity
- Sheet names and column headers are FROZEN. Never rename, reorder, or add columns.
- Schema exceptions require explicit user approval, logged in `Evidence Log`.
- Required sheets: `Guide`, `Assumption Matrix`, `Scoping Matrix`, `MVP Specifications`, `Evidence Log`, `Open Questions`.

## Scoring (strict)
- `+1` confirmed, `+0.5` partial, `0` unclear, `-1` contradicted.
- Aggregate per assumption, then classify:
  - STRONG: sum >= +1.5
  - CONTESTED: any positive AND any negative signal present (overrides STRONG)
  - INVALIDATED: sum <= -0.5
  - WEAK: everything else

## MVP scope gate
- ONLY STRONG assumptions populate `MVP Specifications` and `Scoping Matrix`.
- CONTESTED -> `Open Questions`.
- WEAK and INVALIDATED -> `Evidence Log` only.

## Output style
- Spreadsheet-safe: single-line cells, no markdown, quote commas, no embedded newlines.
- Every assumption cites evidence (transcript line ref or `no-signal`).

## QA gate
- `qa-validator` MUST pass before reporting completion. Stop hook enforces this.

## Step-by-step confirmation (MANDATORY)
After every meaningful artifact (intake, assumptions, interview guide, seeded workbook, signals, scoring, populated workbook, deliverables), STOP and ask the user to confirm or request edits before continuing. Never chain steps without explicit approval. This overrides any skill instruction that says "proceed automatically."

## Writes
- Workbook lives locally at `output/<feature_slug>.xlsx`.
- Writes go through `scripts/workbook.py`. Never edit .xlsx by any other path.
