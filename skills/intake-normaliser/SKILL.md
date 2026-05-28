---
name: intake-normaliser
description: Validate and normalise the feature brief into a structured intake object plus a list of testable assumptions.
---

# intake-normaliser

## Required fields
`feature_name`, `problem_statement`, `target_user`, `hypothesis`, `success_metric`. `notes` is optional.

## Asking style — adaptive

**Detect first**: scan the user's invocation for a structured brief.
- If the user pasted JSON / a labelled block / a clearly structured brief that fills all required fields → parse directly. Do NOT ask questions. Confirm by echoing the parsed values back in one line.
- If the user invoked `/smart-interview` with no brief, OR fields are partially supplied → ask **one field at a time**, in this order:

1. **feature_name** — _"What's the feature called? (short working title)"_
2. **problem_statement** — _"What problem does it solve? Example: 'Traders waste ~15 min/day reconciling end-of-day positions across 3 systems.'"_
3. **target_user** — _"Who specifically feels this pain? Example: 'Sell-side fixed-income traders at tier-2 banks.'"_
4. **hypothesis** — _"What's your bet? Example: 'A unified EOD reconciliation view will cut that to <2 min and reduce break-investigation time by 40%.'"_
5. **success_metric** — _"How will you know it worked? Example: 'Median reconciliation time per trader-day; target ≤2 min within 30 days of GA.'"_
6. **notes** (optional) — _"Anything else worth capturing? (constraints, prior attempts, edge cases). Skip if none."_

Rules for the one-by-one flow:
- One question per turn. Wait for the user's answer before moving on.
- If the answer is vague (one or two words for a problem statement), ask one clarifying follow-up, then accept.
- Never re-ask a field the user already provided in the original invocation.
- After the last field, echo the full parsed intake back in one block for confirmation before moving to assumptions.

## Output

```json
{
  "intake": {
    "feature_name": "...",
    "problem_statement": "...",
    "target_user": "...",
    "hypothesis": "...",
    "success_metric": "...",
    "notes": "..."
  },
  "assumptions": [
    {"id": "A1", "text": "...", "source": "hypothesis"},
    {"id": "A2", "text": "...", "source": "problem_statement"}
  ]
}
```

## Rules for assumptions
- Each must be testable in a customer interview (confirmable / contradictable).
- Split compound claims.
- Tag `source` = which intake field it came from.
- IDs are stable (`A1`, `A2`, ...) — they flow through every sheet.
