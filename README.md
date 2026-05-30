# Smart Interview (Claude Code plugin)

Runs a **multi-interview** user-research study for a single PM: a feature brief becomes an
interview guide, you loop through client calls (one per call), and the plugin scores each
assumption **in code** — with full explainability — then produces an Excel report and a
Word/Markdown PRD with quote-level traceability.

## Install

```bash
# add from the marketplace
/plugin marketplace add LearnerSJ/smart-interview
/plugin install smart-interview@smart-interview

# python deps
python3 -m pip install --user openpyxl python-docx python-pptx
```

Then:

```
/smart-interview
```

## Architecture

- **CLAUDE.md** — global rules loaded into context
- **skills/** — orchestrator + sub-skills (intake, guide, transcript-signal-extractor, qa-validator, deliverable-exporter)
- **scripts/** — the engine:
  - `store.py` — SQLite ledger, the **source of truth** (assumptions, interviews, signals, use cases)
  - `scoring.py` — code-owned verdict: strength / consensus / confidence + explainability
  - `synthesis.py` — weighted prioritisation + saturation
  - `export_xlsx.py` — 6-view Excel report (regenerable view)
  - `prd_export.py` — Word + Markdown PRD
  - `study.py` — CLI entrypoint (all commands below)
- **hooks/** — guardrails (xlsx-via-study.py, QA gate, evidence log)
- **M365 MCP** — read-only calendar + Teams/Gong transcript retrieval

## Workflow

**Phase 1 — Setup (once):** intake → assumptions (categorised) → interview guide → `create-study`.

**Phase 2 — Interview loop (repeat until you stop):**
get transcript → extract signals → **verify** → `add-interview` → `status` →
*"another / add assumption / stop?"*. Append-only; one client per call; resumable.

**Phase 3 — Synthesis (on stop):** `set-usecases` → `synthesise` (prioritisation + saturation)
→ `export` (Excel) + `export-prd` (Word/Markdown).

## CLI

```bash
python3 scripts/study.py create-study   --db output/<slug>.sqlite --payload create.json
python3 scripts/study.py add-interview  --db ... --payload interview.json
python3 scripts/study.py add-assumption --db ... --id A7 --text "..." [--category --priority]
python3 scripts/study.py status         --db ... [--json]
python3 scripts/study.py why            --db ... --id A1
python3 scripts/study.py set-usecases   --db ... --payload usecases.json
python3 scripts/study.py synthesise     --db ...
python3 scripts/study.py export         --db ... [--out output/<slug>.xlsx]
python3 scripts/study.py export-prd     --db ... --format word|md|ppt|all
python3 scripts/study.py qa             --db ...
```

## Scoring (code-owned)

Per assumption, over the interviews that addressed it (weighted by ICP-fit):
**strength** (weighted mean −1..+1), **consensus** (contested vs agreed), **confidence**
(from `n`). Class: CONTESTED ▸ INVALIDATED (≤ −0.34) ▸ STRONG (≥ +0.5 and confident) ▸ WEAK.
`n=1` positives are **WEAK/thin**, not STRONG — count never substitutes for confidence.
Thresholds are configurable per study; `why` explains every verdict with driver/counter quotes.

Outputs: `output/<slug>.sqlite` (truth), `output/<slug>.xlsx`, `output/<slug>_PRD.docx`, `output/<slug>_PRD.md`, `output/<slug>_readout.pptx`.
