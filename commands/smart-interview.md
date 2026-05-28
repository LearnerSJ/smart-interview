---
description: Run the Smart Interview workflow — brief → guide → transcript → scored assumptions → PRD-ready Excel + Word + PPT + Markdown deliverables.
---

Invoke the `smart-interview-start` skill from this plugin to drive the full workflow.

You MUST follow every rule in the plugin's `CLAUDE.md` and the orchestrator skill — including the mandatory step-by-step confirmation gates. After every artifact (intake, assumptions, interview guide, seeded workbook, signals, scoring, populated workbook, deliverables), STOP and wait for explicit user approval before continuing.

Begin Step 1 (Intake) now. If the user provided a structured brief with their `/smart-interview` invocation, parse it; otherwise ask for `feature_name` first and walk fields one at a time per `intake-normaliser`.
