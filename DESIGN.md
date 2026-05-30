# Smart Interview — v0.2.0 Design

Multi-call user-research workflow for a **single PM**, running locally as a Claude Code plugin.
Status: **design / not yet implemented.** Supersedes the single-pass v0.1.0 flow.

## Decisions locked

| # | Decision | Rationale |
|---|---|---|
| A | **Single PM, local store.** No shared service, no network datastore. | Scope kept to one researcher's laptop. Store is designed so it *could* later move behind a service without changing the scoring/export layers. |
| B | **Verdict lives in code, with explainability surfaced to the user.** | A normalised, consensus-aware scoring model is too complex for spreadsheet formulas. Code owns the logic; every verdict ships with a human-readable rationale and its contributing signals. We therefore **drop the reference file's live `IF`/`SUM` formulas** and write computed *values* + an `Explanation` column instead. |

## Core principle: store long, present wide

The source of truth is a **tidy, append-only evidence ledger** — one row per signal.
The reference Excel's `C1…C10` matrix is a **generated view** (pivot) of that ledger, not the store.
This removes the 10-interview cap, survives editing, and lets each interview carry metadata.

```
┌─ Orchestration ── looping workflow + human-in-the-loop gates (the skill)
├─ Presentation ─── Excel (ref layout) · Word PRD · PPT · Markdown   ← regenerable VIEWS
├─ Aggregation ──── pure scoring fn: ledger → {strength, consensus, confidence, class, why}
└─ Data (truth) ─── study.json  +  evidence.jsonl   (local, versioned, human-readable)
```

## Data model

All under `output/<slug>/`.

### `study.json` — config + registry (mutable, small)
```jsonc
{
  "slug": "real-time-position-reconciliation-dashboard",
  "intake": { "feature_name": "...", "problem_statement": "...", "target_user": "...",
              "hypothesis": "...", "success_metric": "..." },
  "assumptions": [
    { "id": "A1", "text": "...", "category": "W", "priority": "High",
      "source": "problem_statement", "created_at_interview": 0 }
  ],
  "guide": [ { "question_id": "Q1", "section": "Probe", "text": "...", "assumption_ids": ["A1"] } ],
  "interviews": [
    { "id": "C1", "label": "Client A — buy-side PM", "segment": "mid-size AM",
      "icp_fit": 1.0, "date": "2026-05-21", "consent_recorded": true,
      "transcript_ref": "gong://...", "added_at": "2026-05-29T..." }
  ],
  "scoring": {                          // config, NOT hard-coded constants
    "strong_strength": 0.5, "invalidated_strength": -0.34,
    "contested_min_share": 0.3, "confidence_n": { "medium": 3, "high": 5 }
  }
}
```

### `evidence.jsonl` — the ledger (append-only, one signal per line)
```jsonc
{ "interview_id": "C1", "assumption_id": "A1", "polarity": 1, "score": 1.0,
  "quote": "I lose 20 minutes every morning reconciling...", "line_ref": "L42",
  "extracted_by": "model", "verified": true, "ts": "2026-05-29T..." }
```
Append-only = natural audit trail. Re-scoring never mutates it. `verified` flips true only after the human gate (§ scoring step 3).

## Scoring model (code-owned, explainable)

For each assumption, over the `n` interviews that addressed it (weight `w_i` = interviewee `icp_fit`, stance `s_i ∈ {-1, 0, +0.5, +1}`):

- **Strength** `S = Σ(wᵢ·sᵢ) / Σ(wᵢ)`  → weighted mean, range −1…+1 (independent of how many interviews — fixes the "SUM rewards volume" bug).
- **Consensus** from sign distribution: `pos_share`, `neg_share`. High disagreement ⇒ CONTESTED.
- **Confidence** from `n` (+ total weight): Low `n<3`, Medium `3–4`, High `≥5`.

**Classification (thresholds from `study.json.scoring`):**
```
CONTESTED     if pos_share ≥ τ AND neg_share ≥ τ        (material support both ways)
STRONG        elif S ≥ strong_strength AND confidence ≥ Medium
INVALIDATED   elif S ≤ invalidated_strength
WEAK          otherwise (weak signal, or too few interviews)
```

**Explainability (decision B):** the scorer returns, per assumption, an `Explanation` string plus the contributing signals, e.g.
> `STRONG — weighted mean +0.71 across n=6 (6/6 positive, high consensus); confidence High.`

Surfaced three ways: a `why <id>` command (full breakdown + every quote), an `Explanation` column in the Excel view, and the PRD's traceability links. **No verdict is ever a black box.**

## Commands (`scripts/workbook.py` → grows into a study CLI)

| Command | Does | Idempotency |
|---|---|---|
| `create-study --slug --intake … --guide … --assumptions …` | Init `study.json` + empty `evidence.jsonl`; render empty export workbook (reference layout). | Refuses if study exists unless `--force`. **Created once, with the guide.** |
| `add-interview --slug --id C_n --meta … --signals payload.json` | Register interview in `study.json`; append verified signals to ledger; recompute; write into the **next** client column of the view. | Refuses duplicate interview id. Never re-seeds. |
| `add-assumption --slug --text … --category …` | Append assumption mid-study; flag earlier interviews for **back-fill** recheck. | — |
| `status --slug` | Dashboard: per-assumption class + strength/consensus/confidence + **saturation hint**. | read-only |
| `why --slug --assumption A3` | Full rationale + contributing signals/quotes. | read-only |
| `synthesise --slug` | Saturation report → weighted **Use Case Priority** → **PRD** (STRONG-and-confident only) with quote-level traceability → regenerate all exports. | run on "stop" |
| `export --slug --format excel\|word\|ppt\|md\|all` | Regenerate views from the store. | pure function of store |

## Workflow (the loop)

1. **Setup (once):** intake → assumptions → guide → `create-study`. Store + empty exports born together.
2. **Interview loop (repeat until stop):**
   `ingest transcript (paste / Gong / M365) → extract signals → ` **🛑 human verifies each signal vs its quote** ` → add-interview → recompute → status → ask: another / add-assumption / stop?`
   Resumable across sessions: reads existing store, knows the next interview index, never clobbers.
3. **Synthesis (on stop):** `synthesise` → saturation, prioritisation, PRD, exports.

## Saturation & emergent assumptions

- **Saturation hint** in `status`: if the last *k* interviews changed no classification, flag likely saturation per category, and call out thin areas (`confidence Low, n=2`).
- **Emergent assumptions:** `add-assumption` is first-class; back-fill prompts ensure earlier interviews get rechecked rather than silently under-counted.

## Compliance (scoped to single-PM local)

Lighter than a shared service, but not skipped:
- `consent_recorded` per interview; `add-interview` warns if false.
- Optional **redaction/pseudonymisation** pass (`Client A — buy-side PM`) before PRD export.
- Local-only storage; **retention** = an explicit `purge-transcripts` step that drops raw text but keeps coded signals.
- Append-only ledger doubles as the audit trail.
- Note: SmartStream records via **Gong** — prefer Gong as the ingestion + consent/retention source of record rather than re-solving it.

## Migration from v0.1.0

- Retire the frozen 6-sheet schema and the in-place-overwrite `write`.
- `qa-validator` repurposed: validate **ledger ↔ export consistency** and MVP purity (STRONG-only) against computed verdicts, rather than the old single-aggregate checks.
- Export's Assumption Matrix adopts the reference layout (`C1…C10` + Score/Signal/Recommendation + **Explanation**) as a generated view with computed values.

## Open questions for sign-off

1. **Store format** — JSONL+JSON (proposed: transparent, git-diffable, zero deps) vs SQLite (queryable, scales further). Recommend JSONL for single-PM.
2. **One stance per (interview, assumption)?** If a transcript supports an assumption in one breath and undercuts it in another, do we record two signals (and let consensus reflect the tension) or force one net stance per interview? Recommend: record both; it's more honest.
3. **Interview weighting** — default `icp_fit = 1.0` for everyone, or force the PM to set it per interview? Recommend default 1.0, optional override.
4. **PPT** — still wanted, or is Word PRD + Excel + Markdown enough for v0.2.0?
```
