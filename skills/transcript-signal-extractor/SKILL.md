---
name: transcript-signal-extractor
description: Parse an interview transcript and extract polarity-tagged signals against each assumption.
---

# transcript-signal-extractor

## Inputs
- `assumptions[]`
- transcript text (with line numbers or timestamps). Source options:
  - user paste / local file
  - M365 MCP: `sharepoint_search` to locate the `.docx` or `.vtt`, then `read_resource`

## Output

```json
[
  {
    "assumption_id": "A1",
    "quote": "verbatim from transcript",
    "line_ref": "L42",
    "polarity": 1,
    "rationale": "one-line why this polarity"
  }
]
```

## Rules
- Quote VERBATIM. Never paraphrase.
- One signal per quote. A quote that touches multiple assumptions emits multiple signals.
- `polarity` in {+1, +0.5, 0, -1} per CLAUDE.md.
- If an assumption has no signal, emit one row `{polarity: 0, quote: "", line_ref: "no-signal"}` so the gap is recorded.
- Ignore interviewer statements unless the customer responds confirmingly/contradictingly.
- Never invent line refs. If no line numbers, use timestamp like `T00:12:34`.
