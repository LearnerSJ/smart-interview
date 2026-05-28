---
name: smart-interview-start
description: Orchestrator for the Smart Interview workflow. Drives intake -> guide -> transcript -> scoring -> workbook -> QA. Trigger on /smart-interview, "run smart interview", or "process interview transcript".
---

# smart-interview-start

You orchestrate the full workflow. Read `CLAUDE.md` for non-negotiable rules.

## Steps (run in order) — STOP and confirm after EACH

Each step ends with a hard gate: show the artifact, ask the user to confirm or edit, and wait. Do NOT chain steps. This rule overrides any skill that says "proceed automatically."

1. **Intake** -> `intake-normaliser`
   🛑 GATE: echo parsed intake; ask "Confirm or edit?" Wait.
2. **Assumptions** -> derived from intake
   🛑 GATE: show assumption list with IDs; ask "Accept all, edit, add, drop?" Wait.
3. **Interview guide** -> `interview-guide-generator` (DRAFT ONLY — do not seed workbook yet)
   🛑 GATE: show full guide; ask "Confirm or edit?" Wait.
4. **Seed workbook** -> call `scripts/workbook.py seed`
   🛑 GATE: confirm file path + sheet counts; ask "Looks right?" Wait.
5. **Transcript ingestion** -> `transcript-signal-extractor`
   - User-supplied transcript OR M365 MCP (`outlook_calendar_search` -> `sharepoint_search` -> `read_resource`).
   🛑 GATE: show signal sample (first 5-10 rows); ask "Extraction looks correct?" Wait.
6. **Scoring** -> `scoring-engine`
   🛑 GATE: show score table + classifications; ask "Confirm or flag rescoring?" Wait.
7. **Populate workbook** -> `workbook-mapper` (`scripts/workbook.py write`)
   🛑 GATE: show rows written per sheet; ask "Ready for QA?" Wait.
8. **QA gate** -> `qa-validator` MUST pass before completion
   🛑 GATE: show QA result; on fail, ask user how to proceed.
9. **Deliverables** -> `deliverable-exporter` (Word, PPT, Markdown — only after QA pass)
   🛑 GATE: ask which formats (word / ppt / md / all) BEFORE generating.

## Rules for gates
- One question per gate, phrased plainly: "Confirm to proceed, or tell me what to change."
- Never call the next tool until the user explicitly approves.
- "yes" / "proceed" / "lgtm" / "go" all count as approval.
- Anything else = treat as edit request, do not advance.

## State carried between steps
- `intake`, `assumptions[]`, `signals[]`, `scores{}`, `workbook_path`

## Final response to user (one screen)
- counts: STRONG / CONTESTED / WEAK / INVALIDATED
- MVP features (STRONG only)
- top 3 open questions
- workbook path
