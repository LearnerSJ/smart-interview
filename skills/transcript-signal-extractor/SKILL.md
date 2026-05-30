---
name: transcript-signal-extractor
description: Parse one interview transcript and extract scored, quote-backed signals against each assumption, for the human-verify gate before writing to the study.
---

# transcript-signal-extractor (v0.2)

Extract signals for **one interview** against the study's assumptions, then hand them
to the orchestrator's mandatory VERIFY gate. Output feeds `study.py add-interview`.

## Inputs
- `assumptions[]` (id + text, including any emergent ones)
- transcript text with line numbers or timestamps. Sources:
  - PM paste / local file
  - Gong (preferred — consent/retention already governed there)
  - M365 MCP: `sharepoint_search` for the `.docx`/`.vtt`, then `read_resource`
- interview metadata: role, firm, segment, ICP-fit (0–1), consent (y/n), date

## Output: an interview payload

```json
{
  "interview": {
    "id": "C2", "label": "PM, Beta Capital", "date": "2026-05-23",
    "interviewee_role": "Multi-asset PM", "firm": "Beta", "segment": "mid-size",
    "icp_fit": 0.9, "consent": true, "source": "gong"
  },
  "signals": [
    {"assumption_id": "A1", "score": 1, "polarity": "yes",
     "quote": "verbatim from transcript", "line_ref": "L42"}
  ]
}
```

## Rules
- **Quote VERBATIM.** Never paraphrase. Never invent a quote or a line ref.
- `score` in {+1 (yes), +0.5 (partial), 0 (unclear), -1 (no)}; `polarity` is the word form.
- One signal per (assumption, stance). If a client addresses an assumption more than once,
  emit each quote — the scorer averages within the interview.
- If an assumption was NOT addressed, **emit no row for it** (absence is handled by the
  scorer as lower `n`; do not fabricate a 0 just to fill the grid).
- Ignore interviewer statements unless the client responds confirming/contradicting.
- Use line numbers if present; else timestamps like `T00:12:34`.

## Verify gate (the orchestrator enforces this)
Present every extracted signal with its quote and proposed score. The PM confirms,
edits scores, or removes signals. **Nothing is written until the PM approves** — set
`verified: true` on approved signals. Extraction is non-deterministic; the human is the
final coder of record.
