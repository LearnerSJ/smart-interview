---
name: interview-guide-generator
description: Produce the interview guide from intake + assumptions (draft only; the orchestrator creates the study separately).
---

# interview-guide-generator (v0.2)

## Inputs
`intake`, `assumptions[]`.

## Output: interview guide (DRAFT)
1. **Intro** (60s) — purpose, consent to record, ground rules.
2. **Warm-up** (3 questions) — role + current workflow.
3. **Assumption probes** — >=1 question per assumption. Open-ended, no leading.
4. **Stack-rank** — force-rank top pain points.
5. **Close** — what did we miss, referrals.

Each row: `{question_id, section, text, assumption_ids[]}`. Every assumption probed by >=1 question.

## Hand-off
This skill produces the guide ONLY. It does not create or seed any file. After the PM
confirms the guide, the orchestrator (`smart-interview-start`) creates the study with:

```bash
python3 scripts/study.py create-study --db output/<slug>.sqlite --payload create.json
```

where `create.json` carries `name`, `slug`, `intake`, and `assumptions[]` (each with a
category: W/A/M/T/G). The guide itself is captured in the study intake/notes; questions
are reused verbatim during interviews. Return the guide to the orchestrator for the
confirmation gate.
