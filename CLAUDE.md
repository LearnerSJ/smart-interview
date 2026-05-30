# Smart Interview — Global Rules (v0.2)

These rules apply to every skill, tool call, and output in this workflow.

## Source of truth
- A local **SQLite study** is the single source of truth (`output/<slug>.sqlite`), driven
  ONLY by `scripts/study.py`. Excel / Word / Markdown are regenerable VIEWS — never edited
  by hand, never treated as data.
- The ledger is **append-only**: one row per signal, one row per interview. Re-running does
  not clobber prior interviews. Each client call is recorded once via `add-interview`.

## Scoring (code-owned, explainable)
- Signals score `+1` yes, `+0.5` partial, `0` unclear, `-1` no.
- The verdict is computed in `scripts/scoring.py`, never in spreadsheet formulas. Per
  assumption, over the interviews that addressed it (weighted by interview ICP-fit):
  - **strength** = weighted mean stance (−1..+1)
  - **consensus** = contested when both camps are material; else high/moderate
  - **confidence** = banded by `n` (interviews addressing it)
  - **class**: CONTESTED (disagreement) ▸ INVALIDATED (strength ≤ −0.34) ▸
    STRONG (strength ≥ +0.5 AND confidence ≥ medium) ▸ WEAK (everything else)
- Every verdict ships with a plain-English **why** plus driver/counter quotes
  (`study.py why --id <A>`). Thresholds live in the study's `scoring_config`, not in code.

## Scope gate
- ONLY STRONG-and-confident assumptions feed MVP scope / PRD Feed and prioritisation.
- CONTESTED → Open Questions. WEAK / INVALIDATED → evidence appendix only.

## Evidence & provenance
- Every signal carries a **verbatim quote** and a **line/timestamp ref**. Never paraphrase,
  never invent a ref. Un-addressed assumptions emit no row (handled as lower `n`).
- LLM extraction is non-deterministic: signals are **verified by the PM** before they are
  written to the study. Never write unverified signals.

## Compliance (single-PM, FS/EU)
- Record **consent** per interview; QA fails if any interview lacks it.
- Keep coded signals; treat raw transcripts as transient. Storage is local-only.

## QA gate
- `scripts/study.py qa` MUST pass before reporting completion (consent, provenance,
  STRONG-is-evidenced). The Stop hook enforces this via `hooks/.qa_state`.

## Step-by-step confirmation (MANDATORY)
After every meaningful artifact (intake, assumptions, interview guide, study creation,
each interview's extracted signals, status, synthesis, deliverables), STOP and ask the PM
to confirm or request edits before continuing. Never chain steps without explicit approval.
This overrides any skill instruction that says "proceed automatically."

## Writes
- All study writes go through `scripts/study.py`. Never write the `.xlsx`/`.sqlite` by any
  other path (the schema-guard hook blocks `.xlsx` writes that bypass `study.py`).
