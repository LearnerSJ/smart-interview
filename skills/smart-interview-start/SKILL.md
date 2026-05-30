---
name: smart-interview-start
description: Orchestrator for the Smart Interview workflow (v0.2, single-PM, multi-interview). Drives intake -> guide -> create study -> interview loop -> synthesis -> PRD. Trigger on /smart-interview, "run smart interview", or "process interview transcript".
---

# smart-interview-start (v0.2)

You orchestrate a **single-PM, multi-call** user-research study. The source of truth
is a local SQLite study driven by `scripts/study.py`; the verdict is computed in code
(`scoring.py`) with explainability. Excel / Word / Markdown are regenerable VIEWS.

Read `CLAUDE.md` for non-negotiable rules. **STOP and confirm after EACH artifact** —
never chain steps. This overrides any "proceed automatically" instruction.

## Phase 1 — Setup (run ONCE per study)

1. **Intake** -> `intake-normaliser`. 🛑 GATE: echo parsed intake; "Confirm or edit?" Wait.
2. **Assumptions** -> derived from intake, each tagged with a category
   (W=Workflow, A=AI Readiness, M=MVP Scope, T=Trust/Control, G=Governance).
   🛑 GATE: show list with IDs + categories; "Accept, edit, add, drop?" Wait.
3. **Interview guide** -> `interview-guide-generator` (DRAFT ONLY). 🛑 GATE: show guide; "Confirm or edit?" Wait.
4. **Create study** -> build a `create.json` payload (`name`, `slug`, `intake`,
   `assumptions[]`) and run:
   `python3 scripts/study.py create-study --db output/<slug>.sqlite --payload create.json`
   🛑 GATE: confirm DB path + assumption count. Wait.

## Phase 2 — Interview loop (repeat per client call, until the PM stops)

For EACH interview:

5. **Get the transcript** — pasted by the PM, or pulled via Gong / M365
   (`outlook_calendar_search` -> transcript). Capture interview metadata
   (role, firm, segment, ICP-fit 0–1, consent y/n, date).
6. **Extract signals** -> `transcript-signal-extractor` produces a signals payload
   (one signal per assumption addressed: `score`, `quote`, `line_ref`).
   🛑 **VERIFY GATE (mandatory):** show every extracted signal with its quote; the PM
   confirms/edits/removes before anything is written. LLM extraction is non-deterministic
   — never write unverified signals.
7. **Record it** -> write `interview.json` (interview + verified signals) and run:
   `python3 scripts/study.py add-interview --db ... --payload interview.json`
   (append-only; one client per call; duplicate ids are refused.)
8. **Show updated state** -> `python3 scripts/study.py status --db ...`
   🛑 GATE: show the dashboard + saturation hint, then ask:
   **"Add another interview, add a new assumption, or stop and synthesise?"** Wait.
   - "another" -> back to step 5.
   - "add assumption" -> `study.py add-assumption ...` (flags earlier interviews for
     back-fill), then back to step 5.
   - "stop" -> Phase 3.

Emergent assumptions ARE allowed mid-study (via add-assumption). Use
`study.py why --id <A>` any time to show the full rationale + driver/counter quotes.

## Phase 3 — Synthesis (when the PM stops)

9. **Use cases** -> propose use cases derived from STRONG assumptions; the PM supplies/
   confirms the four dimension scores (Customer Value, Strategic Fit, Feasibility,
   Time-to-Value, each 1–3). Write `usecases.json`; run `study.py set-usecases ...`.
   🛑 GATE: show proposed use cases before scoring. Wait.
10. **Synthesise** -> `python3 scripts/study.py synthesise --db ...` (saturation +
    weighted prioritisation). 🛑 GATE: show result; "Proceed to PRD?" Wait.
11. **Deliverables** -> 🛑 GATE: ask which formats (excel / word / ppt / md / all) FIRST, then:
    `study.py export ...` (Excel report) and `study.py export-prd --format word|md|ppt|all ...`.

## State carried between steps
`slug`, `db_path`, `intake`, `assumptions[]`, `interviews[]`, `scores{}`, `use_cases[]`

## Resuming a study
If `output/<slug>.sqlite` already exists, do NOT re-create it — read `status` to see how
many interviews are recorded and resume the loop at the next call.

## Final response to the PM (one screen)
- counts: STRONG / CONTESTED / WEAK / INVALIDATED + saturation verdict
- MVP scope (STRONG only) with one supporting quote each
- top open questions (CONTESTED)
- prioritised use cases (P1/P2/P3)
- paths: study DB, Excel, PRD
