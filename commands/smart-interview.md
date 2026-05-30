---
description: Run the Smart Interview workflow — brief → guide → looped client interviews → code-scored assumptions → Excel report + Word/Markdown PRD.
---

Invoke the `smart-interview-start` skill from this plugin to drive the full workflow.

You MUST follow every rule in the plugin's `CLAUDE.md` and the orchestrator skill — including the mandatory step-by-step confirmation gates. After every artifact (intake, assumptions, interview guide, study creation, each interview's extracted signals, status, synthesis, deliverables), STOP and wait for explicit user approval before continuing. In particular, never write a transcript's signals to the study until the PM has verified them.

Begin Phase 1, Step 1 (Intake) now. If the user provided a structured brief with their `/smart-interview` invocation, parse it; otherwise ask for `feature_name` first and walk fields one at a time per `intake-normaliser`. If a study DB already exists for this feature, resume the interview loop instead of recreating it.
