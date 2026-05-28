---
name: interview-guide-generator
description: Produce the interview guide and seed the local Excel workbook with the canonical sheet structure.
---

# interview-guide-generator

## Inputs
`intake`, `assumptions[]`.

## Output: interview guide
1. **Intro** (60s) — purpose, consent to record, ground rules.
2. **Warm-up** (3 questions) — role + current workflow.
3. **Assumption probes** — >=1 question per assumption. Open-ended, no leading.
4. **Stack-rank** — force-rank top pain points.
5. **Close** — what did we miss, referrals.

Each row: `{question_id, section, text, assumption_ids[]}`. Every assumption probed by >=1 question.

## Seed the workbook

Run from the plugin root:

```bash
python3 scripts/workbook.py seed \
  --path "output/<feature_slug>.xlsx" \
  --guide guide.json \
  --assumptions assumptions.json
```

`workbook.py seed` creates the file with exactly these sheets/columns:

| Sheet | Columns |
|---|---|
| Guide | question_id, section, text, assumption_ids |
| Assumption Matrix | id, text, source, score, class, evidence_refs |
| Scoping Matrix | use_case_id, description, priority, linked_assumptions |
| MVP Specifications | feature_id, name, description, linked_assumptions |
| Evidence Log | timestamp, assumption_id, quote, line_ref, polarity, score |
| Open Questions | id, question, reason, linked_assumptions |

Populate `Guide` (all questions) and `Assumption Matrix` (id, text, source). Other sheets stay empty until post-interview.

Return `workbook_path`.
