#!/usr/bin/env python3
"""
phase3_reachability.py - post-run analysis of gate reachability and the pysr_prior control.
Reads rows only; makes no API calls and edits nothing in the rows.

    python phase3_reachability.py --rows phase3_out --out /tmp/phase3_reachability.csv

Per (equation, seed) it reports, for each of llm_acceptance and pysr_prior:
  * reachable   - recomputed from the FULL row's llm_r2 (not trusted from the row field)
        llm_acceptance : full llm_r2 >= 0.95  (LLM accepted outright, so the ablation can change it)
        pysr_prior     : 0.5 <= full llm_r2 < 0.95  (seed branch is taken in full)
  * field_ok    - the row's own gate_reachable matches the recomputed value
  * llm_drift   - the ablated arm's llm_r2 differs from full (LLM response not identical, so
                  any difference in outcome is not attributable to the switch alone)
  * mode_changed- llm_mode_used differs between full and ablated
  * far_full / far_abl, rec99_full / rec99_abl (far R2 >= 0.99), changed

The pysr_prior control cannot be proven from rows alone (both arms usually end
hybrid_pysr_better). This script lists reachable pysr_prior cases so you can confirm the
seed was dropped in the run log ("discarding LLM prior" / no "guesses param" line).
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ACCEPT, WINDOW_LO = 0.95, 0.5


def load(p):
    p = Path(p)
    if not p.exists():
        return {}
    out = {}
    for l in p.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            out[(r["equation"], int(r["seed"]))] = r
    return out


def reach(gate, llm_r2):
    if llm_r2 is None:
        return None
    if gate == "llm_acceptance":
        return llm_r2 >= ACCEPT
    return WINDOW_LO <= llm_r2 < ACCEPT


def far(r):
    v = r.get("extrap_r2_far")
    return v if isinstance(v, (int, float)) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="phase3_out")
    ap.add_argument("--out", default="phase3_reachability.csv")
    a = ap.parse_args()
    d = Path(a.rows)
    full = load(d / "full.jsonl")
    if not full:
        print(f"no rows in {d}/full.jsonl", file=sys.stderr)
        return 1
    table = []
    for gate in ("llm_acceptance", "pysr_prior"):
        abl = load(d / f"{gate}.jsonl")
        for key, f in sorted(full.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            g = abl.get(key)
            if g is None:
                continue
            rch = reach(gate, f.get("llm_r2"))
            ff, fa = far(f), far(g)
            table.append({
                "gate": gate, "equation": key[0], "seed": key[1],
                "full_llm_r2": f.get("llm_r2"), "abl_llm_r2": g.get("llm_r2"),
                "reachable": rch, "field_ok": g.get("gate_reachable") == rch,
                "llm_drift": f.get("llm_r2") != g.get("llm_r2"),
                "mode_full": f.get("llm_mode_used"), "mode_abl": g.get("llm_mode_used"),
                "mode_changed": f.get("llm_mode_used") != g.get("llm_mode_used"),
                "far_full": ff, "far_abl": fa,
                "rec99_full": None if ff is None else ff >= 0.99,
                "rec99_abl": None if fa is None else fa >= 0.99,
                "status_full": f.get("status"), "status_abl": g.get("status"),
            })
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        if table:
            w = csv.DictWriter(fh, fieldnames=list(table[0]))
            w.writeheader()
            w.writerows(table)
    print(f"wrote {len(table)} rows to {a.out}\n")
    for gate in ("llm_acceptance", "pysr_prior"):
        rows = [t for t in table if t["gate"] == gate]
        n = len(rows)
        r = [t for t in rows if t["reachable"]]
        ch = [t for t in r if t["rec99_full"] != t["rec99_abl"]]
        print(f"== {gate}: {n} paired cases")
        print(f"   reachable: {len(r)}   unreachable (ties by construction): {n - len(r)}")
        print(f"   reachable AND recovery changed (0.99, far): {len(ch)}")
        print(f"   reachable AND mode changed: {sum(t['mode_changed'] for t in r)}")
        print(f"   gate_reachable field disagrees with recomputed: {sum(not t['field_ok'] for t in rows)}")
        print(f"   LLM drift between arms: {sum(t['llm_drift'] for t in rows)}")
        if gate == "pysr_prior":
            print("   reachable cases to verify in the run log (seed dropped?):")
            for t in r:
                print(f"     {t['equation']} seed {t['seed']}  llm_r2={t['full_llm_r2']:.4f}")
            if not r:
                print("     none: pysr_prior is untestable on this data; report that, not a null effect")
        if gate == "llm_acceptance":
            print("   NOTE: reachable cases are capped by LLM acceptance in full; the sign test needs "
                  ">=7 non-tied equations, so a significant result may be impossible.")
        print()
    bad = [t for t in table if not t["field_ok"]]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
