---
name: scoring-engine
description: Aggregate signals per assumption and classify into STRONG / CONTESTED / WEAK / INVALIDATED.
---

# scoring-engine

## Inputs
`signals[]` from `transcript-signal-extractor`.

## Algorithm

For each assumption:
1. `sum = Sigma(polarity)` across its signals.
2. `has_positive = any(polarity > 0)`; `has_negative = any(polarity < 0)`.
3. Classify (in order):
   - `has_positive AND has_negative` -> **CONTESTED** (precedence)
   - `sum >= 1.5` -> **STRONG**
   - `sum <= -0.5` -> **INVALIDATED**
   - else -> **WEAK**

## Output

```json
{
  "A1": {"sum": 2.0, "class": "STRONG", "signal_count": 3},
  "A2": {"sum": -1.0, "class": "INVALIDATED", "signal_count": 2}
}
```

## Guardrails
- No rounding. Sums are exact.
- Never re-weight signals here. If a signal looks miscategorised, send back to `transcript-signal-extractor`.
