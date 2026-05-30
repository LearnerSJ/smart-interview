#!/usr/bin/env python3
"""Smart Interview v0.2 CLI — single-PM, multi-interview, ledger-backed.

Source of truth is a local SQLite study (see store.py). The verdict is computed
in code (scoring.py) with full explainability. Excel is a regenerable view
(export_xlsx.py).

Subcommands:
  create-study   --db PATH --payload create.json
  add-interview  --db PATH --payload interview.json   (append-only; one client per call)
  add-assumption --db PATH --id A7 --text "..." [--category --priority]
  status         --db PATH [--json]                   (dashboard + saturation hint)
  why            --db PATH --id A1                     (full rationale + quotes)
  export         --db PATH [--out PATH]                (regenerate the Excel view)

Payload shapes:
  create.json   {name, slug, intake{}, assumptions[{id,text,category,priority}], scoring_config{}}
  interview.json{interview{id,label,date,interviewee_role,firm,segment,icp_fit,consent,source,transcript_ref},
                 signals[{assumption_id,score,polarity,quote,line_ref,verified}]}
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

import store, scoring, export_xlsx, synthesis, prd_export, ppt_export

QA_STATE = Path(__file__).resolve().parent.parent / "hooks" / ".qa_state"


def _helpers(conn):
    s = store.get_study(conn)
    return {
        "assumptions": store.list_assumptions(conn),
        "interviews": store.list_interviews(conn),
        "scoring_config": s["scoring_config"],
        "signals": lambda aid: store.list_signals(conn, aid),
    }


def cmd_create_study(args):
    p = json.loads(Path(args.payload).read_text())
    conn = store.connect(args.db)
    if store.study_exists(conn) and not args.force:
        sys.exit("study already exists; pass --force to recreate (this wipes the DB)")
    if args.force:
        for t in ("signals", "interviews", "assumptions", "study"):
            conn.execute(f"DELETE FROM {t}")
        conn.commit()
    store.create_study(conn, p["name"], p["slug"], p.get("intake"),
                        p.get("assumptions"), p.get("scoring_config"))
    print(json.dumps({"created": p["slug"], "db": str(Path(args.db)),
                      "assumptions": len(p.get("assumptions", []))}))


def cmd_add_interview(args):
    p = json.loads(Path(args.payload).read_text())
    conn = store.connect(args.db)
    if not store.study_exists(conn):
        sys.exit("no study in this DB — run create-study first")
    res = store.add_interview(conn, p["interview"], p.get("signals", []))
    print(json.dumps(res))


def cmd_add_assumption(args):
    conn = store.connect(args.db)
    n_iv = len(store.list_interviews(conn))
    store.add_assumption(conn, args.id, args.text, args.category, args.priority,
                         created_at_interview=str(n_iv))
    note = (f"flag earlier {n_iv} interview(s) for back-fill" if n_iv else "no prior interviews")
    print(json.dumps({"added": args.id, "backfill": note}))


def cmd_status(args):
    conn = store.connect(args.db)
    scores = scoring.score_all(_helpers(conn))
    interviews = store.list_interviews(conn)
    counts = {}
    for v in scores.values():
        counts[v["class"]] = counts.get(v["class"], 0) + 1
    if args.json:
        print(json.dumps({"n_interviews": len(interviews), "counts": counts,
                          "scores": scores}, indent=2))
        return
    print(f"\nStudy: {store.get_study(conn)['name']}  |  interviews: {len(interviews)}")
    print("  " + "  ".join(f"{k}={counts.get(k,0)}" for k in
                           ("STRONG", "CONTESTED", "WEAK", "INVALIDATED")))
    print("-" * 92)
    for aid, v in scores.items():
        st = "  n/a" if v["strength"] is None else f"{v['strength']:+.2f}"
        print(f"  {aid:<4} {v['class']:<11} strength={st}  conf={v['confidence']:<6} n={v['n']}")
    low = [a for a, v in scores.items() if v["confidence"] in ("low", "none")]
    if low:
        print(f"\n  Saturation: {len(low)} assumption(s) still thin (n<=2): {', '.join(low)}")


def cmd_why(args):
    conn = store.connect(args.db)
    scores = scoring.score_all(_helpers(conn))
    v = scores.get(args.id)
    if not v:
        sys.exit(f"unknown assumption {args.id}")
    print(f"\n{args.id} — {v['class']}\n{v['why']}\n")
    if v["drivers"]:
        print("Drivers:")
        for d in v["drivers"]:
            print(f"  ({d['score']:+}) [{d['interview_id']} {d.get('line_ref') or ''}] {d.get('quote') or ''}")
    if v["counters"]:
        print("Counter-signals:")
        for d in v["counters"]:
            print(f"  ({d['score']:+}) [{d['interview_id']} {d.get('line_ref') or ''}] {d.get('quote') or ''}")


def cmd_export(args):
    conn = store.connect(args.db)
    s = store.get_study(conn)
    out = args.out or f"output/{s['slug']}.xlsx"
    scores = scoring.score_all(_helpers(conn))
    ranked = synthesis.prioritise(store.list_use_cases(conn))
    export_xlsx.build(out, s, store.list_assumptions(conn), store.list_interviews(conn),
                      store.list_signals(conn), scores, ranked)
    print(json.dumps({"exported": out, "sheets": 6}))


def cmd_set_usecases(args):
    p = json.loads(Path(args.payload).read_text())
    conn = store.connect(args.db)
    store.set_use_cases(conn, p["use_cases"])
    print(json.dumps({"use_cases": len(p["use_cases"])}))


def cmd_synthesise(args):
    conn = store.connect(args.db)
    scores = scoring.score_all(_helpers(conn))
    interviews = store.list_interviews(conn)
    ranked = synthesis.prioritise(store.list_use_cases(conn))
    sat = synthesis.saturation(scores, interviews)
    print(f"\nSaturation: {sat['verdict']}")
    print(f"  STRONG={len(sat['strong'])}  CONTESTED={len(sat['contested'])}  "
          f"thin={len(sat['thin'])}  needs-more={len(sat['needs_more'])}")
    if ranked:
        print("\nPrioritisation:")
        for u in ranked:
            print(f"  {u['priority']}  {u['weighted_score']:>5}  {u['name']}")
    else:
        print("\n(no use cases set — run set-usecases to enable prioritisation)")


def cmd_export_prd(args):
    conn = store.connect(args.db)
    s = store.get_study(conn)
    scores = scoring.score_all(_helpers(conn))
    assumptions = store.list_assumptions(conn)
    interviews = store.list_interviews(conn)
    signals = store.list_signals(conn)
    ranked = synthesis.prioritise(store.list_use_cases(conn))
    sat = synthesis.saturation(scores, interviews)
    written = []
    fmt = args.format
    if fmt in ("md", "all"):
        out = args.out_md or f"output/{s['slug']}_PRD.md"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(prd_export.build_markdown(s, scores, assumptions, interviews, signals, ranked, sat))
        written.append(out)
    if fmt in ("word", "all"):
        out = args.out_word or f"output/{s['slug']}_PRD.docx"
        prd_export.build_word(out, s, scores, assumptions, interviews, signals, ranked, sat)
        written.append(out)
    if fmt in ("ppt", "all"):
        out = args.out_ppt or f"output/{s['slug']}_readout.pptx"
        ppt_export.build_pptx(out, s, scores, assumptions, interviews, signals, ranked, sat)
        written.append(out)
    print(json.dumps({"prd_written": written}))


def cmd_qa(args):
    conn = store.connect(args.db)
    if not store.study_exists(conn):
        sys.exit("no study in this DB")
    interviews = store.list_interviews(conn)
    signals = store.list_signals(conn)
    scores = scoring.score_all(_helpers(conn))
    failures, warnings = [], []

    for iv in interviews:                                   # consent (FS/EU)
        if not iv.get("consent"):
            failures.append(f"consent: interview {iv['id']} has no consent on record")
    for s in signals:                                       # provenance
        if not (s.get("quote") and s.get("line_ref")):
            failures.append(f"provenance: signal {s['id']} missing quote or line_ref")
    for aid, v in scores.items():                           # STRONG must be evidenced
        if v["class"] == "STRONG" and not any(
                s["assumption_id"] == aid and s["score"] > 0 for s in signals):
            failures.append(f"strong-evidence: {aid} is STRONG with no positive signal")
    thin = [a for a, v in scores.items() if v["confidence"] in ("low", "none")]
    if thin:
        warnings.append("thin (n<=2): " + ", ".join(thin))

    QA_STATE.parent.mkdir(parents=True, exist_ok=True)
    if failures:
        QA_STATE.write_text("fail " + " | ".join(failures))
        print(json.dumps({"pass": False, "failures": failures, "warnings": warnings}, indent=2))
        sys.exit(1)
    QA_STATE.write_text("pass " + scoring.__name__)  # marker; content unused beyond prefix
    print(json.dumps({"pass": True, "failures": [], "warnings": warnings}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create-study"); c.add_argument("--db", required=True); c.add_argument("--payload", required=True); c.add_argument("--force", action="store_true"); c.set_defaults(fn=cmd_create_study)
    c = sub.add_parser("add-interview"); c.add_argument("--db", required=True); c.add_argument("--payload", required=True); c.set_defaults(fn=cmd_add_interview)
    c = sub.add_parser("add-assumption"); c.add_argument("--db", required=True); c.add_argument("--id", required=True); c.add_argument("--text", required=True); c.add_argument("--category"); c.add_argument("--priority"); c.set_defaults(fn=cmd_add_assumption)
    c = sub.add_parser("status"); c.add_argument("--db", required=True); c.add_argument("--json", action="store_true"); c.set_defaults(fn=cmd_status)
    c = sub.add_parser("why"); c.add_argument("--db", required=True); c.add_argument("--id", required=True); c.set_defaults(fn=cmd_why)
    c = sub.add_parser("export"); c.add_argument("--db", required=True); c.add_argument("--out"); c.set_defaults(fn=cmd_export)
    c = sub.add_parser("set-usecases"); c.add_argument("--db", required=True); c.add_argument("--payload", required=True); c.set_defaults(fn=cmd_set_usecases)
    c = sub.add_parser("synthesise"); c.add_argument("--db", required=True); c.set_defaults(fn=cmd_synthesise)
    c = sub.add_parser("export-prd"); c.add_argument("--db", required=True); c.add_argument("--format", choices=["word","md","ppt","all"], default="all"); c.add_argument("--out-md"); c.add_argument("--out-word"); c.add_argument("--out-ppt"); c.set_defaults(fn=cmd_export_prd)
    c = sub.add_parser("qa"); c.add_argument("--db", required=True); c.set_defaults(fn=cmd_qa)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
