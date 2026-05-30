#!/usr/bin/env python3
"""Code-owned scoring with explainability (v0.2).

The verdict is computed here, never in spreadsheet formulas. Every classification
ships with the numbers behind it (strength / consensus / confidence), the signals
that drove it, the signals that counter it, and a plain-English rationale — so a
human can always trace verdict -> numbers -> exact quotes.

Per assumption, over the interviews that addressed it:
  - signals are averaged WITHIN an interview, then combined ACROSS interviews
    weighted by interview ICP-fit.
  - strength   = weighted mean stance, range -1..+1
  - consensus  = "contested" when both positive and negative camps are material,
                 else "high"/"moderate" from how lopsided the split is
  - confidence = from n (interviews addressing it), banded by config
  - class      = STRONG / CONTESTED / WEAK / INVALIDATED via config thresholds
"""
from __future__ import annotations
from statistics import mean


def _band_confidence(n, cfg):
    if n <= cfg["confidence_low_max_n"]:
        return "low"
    if n <= cfg["confidence_medium_max_n"]:
        return "medium"
    return "high"


def score_assumption(assumption, interviews_by_id, signals, cfg):
    """Return a rationale dict for one assumption from its signals."""
    # group signals by interview, average score within an interview
    by_iv = {}
    for s in signals:
        by_iv.setdefault(s["interview_id"], []).append(s)

    stances = []  # (interview_id, stance, weight)
    for iid, sigs in by_iv.items():
        stance = mean(s["score"] for s in sigs)
        weight = float(interviews_by_id.get(iid, {}).get("icp_fit", 1.0))
        stances.append((iid, stance, weight))

    n = len(stances)
    if n == 0:
        return {
            "assumption_id": assumption["id"], "n": 0, "strength": None,
            "consensus": "none", "confidence": "none", "class": "WEAK",
            "pos_share": 0.0, "neg_share": 0.0, "drivers": [], "counters": [],
            "why": "No interview has addressed this assumption yet.",
        }

    W = sum(w for _, _, w in stances) or 1.0
    strength = sum(st * w for _, st, w in stances) / W
    pos_share = sum(w for _, st, w in stances if st > 0) / W
    neg_share = sum(w for _, st, w in stances if st < 0) / W

    minority = cfg["contested_minority_share"]
    contested = pos_share >= minority and neg_share >= minority
    confidence = _band_confidence(n, cfg)

    if contested:
        cls = "CONTESTED"
    elif strength <= cfg["invalidated_strength_max"]:
        cls = "INVALIDATED"
    elif strength >= cfg["strong_strength_min"] and confidence in ("medium", "high"):
        cls = "STRONG"
    else:
        cls = "WEAK"

    if contested:
        consensus = "contested"
    elif max(pos_share, neg_share) >= 0.8:
        consensus = "high"
    else:
        consensus = "moderate"

    # drivers (support the leaning) vs counters (oppose it)
    lean = 1 if strength >= 0 else -1
    drivers, counters = [], []
    for s in sorted(signals, key=lambda x: abs(x["score"]), reverse=True):
        ref = {"interview_id": s["interview_id"], "score": s["score"],
               "quote": s.get("quote"), "line_ref": s.get("line_ref")}
        if s["score"] != 0 and (1 if s["score"] > 0 else -1) == lean:
            drivers.append(ref)
        elif s["score"] != 0:
            counters.append(ref)

    why = _explain(cls, strength, n, pos_share, neg_share, consensus, confidence)
    return {
        "assumption_id": assumption["id"], "n": n, "strength": round(strength, 3),
        "consensus": consensus, "confidence": confidence, "class": cls,
        "pos_share": round(pos_share, 3), "neg_share": round(neg_share, 3),
        "drivers": drivers[:5], "counters": counters[:5], "why": why,
    }


def _pct(x):
    return f"{round(x * 100)}%"


def _explain(cls, strength, n, pos, neg, consensus, confidence):
    s = f"{cls}: mean stance {strength:+.2f} across n={n} interview(s); "
    s += f"{_pct(pos)} positive / {_pct(neg)} negative ({consensus} consensus); "
    s += f"{confidence} confidence (n={n})."
    if cls == "CONTESTED":
        s += " Material support on both sides — route to Open Questions, not MVP."
    elif cls == "STRONG":
        s += " Eligible for MVP scope."
    elif cls == "WEAK" and confidence == "low":
        s += " Leaning is unconfirmed — needs more interviews before a call."
    elif cls == "INVALIDATED":
        s += " Net-negative — challenge or drop the hypothesis."
    return s


def score_all(conn_helpers):
    """conn_helpers: a dict with assumptions[], interviews[], signals(aid) callable."""
    assumptions = conn_helpers["assumptions"]
    interviews_by_id = {iv["id"]: iv for iv in conn_helpers["interviews"]}
    cfg = conn_helpers["scoring_config"]
    out = {}
    for a in assumptions:
        sigs = conn_helpers["signals"](a["id"])
        out[a["id"]] = score_assumption(a, interviews_by_id, sigs, cfg)
    return out
