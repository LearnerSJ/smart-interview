#!/usr/bin/env python3
"""Synthesis stage (v0.2): prioritisation + saturation, computed in code.

Runs when the PM decides to stop gathering feedback. Two pure functions:
  - prioritise(): weighted Use Case scoring -> ranked priority tiers
  - saturation(): how confident/settled the study is, what's still thin
"""
from __future__ import annotations

WEIGHTS = {  # must sum to 1.0; mirrors the reference workbook
    "customer_value": 0.35,
    "strategic_fit": 0.25,
    "feasibility": 0.25,
    "time_to_value": 0.15,
}


def prioritise(use_cases, weights=None):
    """Return use cases with a weighted score and P1/P2/P3 tier, ranked."""
    w = {**WEIGHTS, **(weights or {})}
    out = []
    for u in use_cases:
        dims = {k: float(u.get(k) or 0) for k in WEIGHTS}
        score = round(sum(dims[k] * w[k] for k in WEIGHTS), 3)
        out.append({**u, "weighted_score": score})
    out.sort(key=lambda x: x["weighted_score"], reverse=True)
    # tier by score on a 1-3 input scale: >=2.5 P1, >=2.0 P2, else P3
    for u in out:
        s = u["weighted_score"]
        u["priority"] = "P1" if s >= 2.5 else "P2" if s >= 2.0 else "P3"
    return out


def saturation(scores, interviews):
    """Summarise study maturity: counts, thin assumptions, contested items."""
    n = len(interviews)
    thin = [a for a, v in scores.items() if v["confidence"] in ("low", "none")]
    contested = [a for a, v in scores.items() if v["class"] == "CONTESTED"]
    strong = [a for a, v in scores.items() if v["class"] == "STRONG"]
    # near-threshold STRONG candidates that just need more interviews
    almost = [a for a, v in scores.items()
              if v["class"] == "WEAK" and v["strength"] is not None
              and v["strength"] >= 0.5 and v["confidence"] == "low"]
    if n == 0:
        verdict = "No interviews yet."
    elif thin or almost:
        verdict = (f"Not saturated: {len(thin)} assumption(s) still thin"
                   + (f", {len(almost)} positive-but-unconfirmed" if almost else "") + ".")
    elif contested:
        verdict = f"Coverage adequate, but {len(contested)} assumption(s) remain CONTESTED."
    else:
        verdict = "Looks saturated: every assumption has adequate, settled coverage."
    return {"n_interviews": n, "strong": strong, "contested": contested,
            "thin": thin, "needs_more": almost, "verdict": verdict}
