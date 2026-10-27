#!/usr/bin/env python3
"""
phase3_close.py - closure gate for Option 3 / Phase 3 (leave-one-gate-out ablation).

Takes per-case results for the full HDS v50_2 configuration and for each
leave-one-out configuration, verifies the ablation is controlled, and reports each
component's measured contribution. Writes:

    phase3_closure.json     checks, per-component results, input hashes
    phase3_components.csv   one row per ablated component
    PHASE3_CLOSED           marker, written ONLY if every blocking check passes

Exit code 0 = closed, 1 = not closed, 2 = bad input.

Components (Option 3, Phase 3): llm_acceptance, probe, complexity_routing,
nn_augmentation, blend_weight, pysr_prior. Any component not run must be declared with
--omit name:reason so the omission is recorded rather than silent.

Input: JSONL or JSON list, one record per (ablated_component, equation, seed).
Required fields:
    ablated_component  null/"none"/"full" for the full config, else the component removed
    config_diff        list of settings that differ from the full config; must equal
                       [ablated_component] for ablations and [] for the full config
    equation, seed, split_id, r2, status, formula, generation_path, llm_called,
    bypass_used, runtime_s, timeout_s, model_id, code_version, evaluator_version

Usage:
    python phase3_close.py --results results/ablation/*.jsonl \
        --phase2-manifest phase2_out/phase2_closure.json --out-dir phase3_out
"""
import argparse
import csv
import glob
import hashlib
import json
import math
import os
import random
import statistics
import sys
from datetime import datetime, timezone

COMPONENTS = ["llm_acceptance", "probe", "complexity_routing",
              "nn_augmentation", "blend_weight", "pysr_prior"]
FULL_LABELS = {None, "", "none", "full"}
REQUIRED = ["ablated_component", "config_diff", "equation", "seed", "split_id", "r2",
            "status", "formula", "generation_path", "llm_called", "bypass_used",
            "runtime_s", "timeout_s", "model_id", "code_version", "evaluator_version"]
NULLABLE = {"ablated_component", "r2", "formula"}


# ----------------------------------------------------------------- helpers
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expand(patterns):
    out = []
    for p in patterns:
        hits = sorted(glob.glob(p))
        out.extend(hits if hits else [p])
    return out


def load_records(files):
    recs = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            continue
        data = json.loads(text) if text[0] == "[" else [json.loads(l) for l in text.splitlines() if l.strip()]
        for d in data:
            d["_file"] = fp
        recs.extend(data)
    return recs


def as_r2(v):
    if v is None:
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def comp_of(r):
    c = r.get("ablated_component")
    return "full" if c in FULL_LABELS else str(c)


class Report:
    def __init__(self):
        self.checks = []

    def add(self, name, passed, detail="", blocking=True):
        self.checks.append({"name": name, "passed": bool(passed), "blocking": blocking, "detail": detail})

    @property
    def closed(self):
        return all(c["passed"] for c in self.checks if c["blocking"])


def exact_sign_p(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, returned in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


# ------------------------------------------------------------------ checks
def run_checks(recs, args, omitted, rep):
    bad = [f"{r.get('_file','?')}: missing/null '{k}'" for r in recs for k in REQUIRED
           if k not in r or (r[k] is None and k not in NULLABLE)]
    rep.add("schema complete", not bad, f"{len(bad)} problems; first: {bad[:3]}" if bad else f"{len(recs)} records OK")
    if bad:
        return None

    by = {}
    for r in recs:
        by.setdefault(comp_of(r), []).append(r)
    rep.add("full configuration present", "full" in by, f"configs found: {sorted(by)}")
    if "full" not in by:
        return None

    unknown = sorted(set(by) - {"full"} - set(COMPONENTS))
    rep.add("ablated components are recognised names", not unknown, f"unknown: {unknown}")

    covered = set(by) - {"full"}
    missing = [c for c in COMPONENTS if c not in covered and c not in omitted]
    rep.add("every component run or explicitly omitted with a reason", not missing,
            f"missing (neither run nor --omit): {missing}; omitted: {omitted}")

    idx = {}
    for comp, rows in by.items():
        d, dups = {}, []
        for r in rows:
            k = (r["equation"], int(r["seed"]))
            if k in d:
                dups.append(k)
            d[k] = r
        rep.add(f"[{comp}] no duplicate (equation, seed) rows", not dups, f"{len(dups)} duplicates; first: {dups[:3]}")
        idx[comp] = d

    full_keys = set(idx["full"])
    for comp in sorted(covered):
        miss = sorted(full_keys - set(idx[comp]))
        extra = sorted(set(idx[comp]) - full_keys)
        rep.add(f"[{comp}] same equations x seeds as full", not miss and not extra,
                f"missing {len(miss)} {miss[:3]}; extra {len(extra)} {extra[:3]}")
        sp = [k for k in full_keys & set(idx[comp]) if idx[comp][k]["split_id"] != idx["full"][k]["split_id"]]
        rep.add(f"[{comp}] identical split_id as full", not sp, f"{len(sp)} mismatches; first: {sp[:3]}")
        want = [] if comp == "full" else [comp]
        wrong = [k for k, r in idx[comp].items() if sorted(r["config_diff"]) != want]
        rep.add(f"[{comp}] config differs from full ONLY by this component", not wrong,
                f"{len(wrong)} rows with other config changes; first: {wrong[:3]}")
    wrong_full = [k for k, r in idx["full"].items() if list(r["config_diff"]) != []]
    rep.add("[full] config_diff is empty", not wrong_full, f"{len(wrong_full)} rows")

    seeds = sorted({k[1] for k in full_keys})
    rep.add(f"at least {args.min_seeds} seeds", len(seeds) >= args.min_seeds, f"seeds: {seeds}")

    for field in ("model_id", "code_version", "evaluator_version", "timeout_s"):
        vals = sorted({str(r[field]) for r in recs})
        rep.add(f"single {field} across all configurations", len(vals) == 1, f"values: {vals[:5]}")

    if not args.allow_bypass:
        byp = [(comp_of(r), r["equation"], r["seed"]) for r in recs
               if r["bypass_used"] or "bypass" in str(r["generation_path"]).lower()]
        rep.add("no hardcoded/ground-truth bypass rows in any configuration", not byp,
                f"{len(byp)} rows; first: {byp[:3]}")
    nof = [(comp_of(r), r["equation"], r["seed"]) for r in recs
           if r["status"] == "ok" and not str(r.get("formula") or "").strip()]
    rep.add("formula stored for every ok row", not nof, f"{len(nof)} rows; first: {nof[:3]}")
    over = [(comp_of(r), r["equation"], r["seed"]) for r in recs
            if float(r["runtime_s"]) > float(r["timeout_s"]) * 1.05 and r["status"] != "timeout"]
    rep.add("runtime within timeout_s (or labelled timeout)", not over, f"{len(over)} rows; first: {over[:3]}")

    # Tie to Phase 2: the full config here must reproduce the Phase 2 HDS result.
    if args.phase2_manifest:
        try:
            with open(args.phase2_manifest, encoding="utf-8") as f:
                p2 = json.load(f)
            rep.add("Phase 2 manifest says closed", p2.get("closed") is True, f"closed={p2.get('closed')}")
            key = f"recovery_r2>={args.threshold}"
            b_rate = (p2.get("paired_summary") or {}).get(key, {}).get("b_rate")
            if b_rate is None:
                rep.add("Phase 2 recovery available for comparison", False, f"'{key}' not in Phase 2 summary")
            else:
                full_rate = statistics.mean(
                    1.0 if (as_r2(r["r2"]) is not None and r["status"] == "ok" and as_r2(r["r2"]) >= args.threshold) else 0.0
                    for r in idx["full"].values())
                rep.add("full config reproduces Phase 2 HDS recovery", abs(full_rate - b_rate) <= args.reproduce_tol,
                        f"Phase 3 full={full_rate:.4f}, Phase 2 HDS={b_rate:.4f}, tol={args.reproduce_tol}")
        except (OSError, json.JSONDecodeError) as e:
            rep.add("Phase 2 manifest readable", False, str(e))
    else:
        rep.add("Phase 2 manifest supplied (--phase2-manifest)", False,
                "not supplied; full config not tied to Phase 2", blocking=args.require_phase2)
    return idx


# ------------------------------------------------------------- statistics
def analyse(idx, args):
    full = idx["full"]
    eqs = sorted({k[0] for k in full})
    seeds = sorted({k[1] for k in full})

    def per_eq(d, pred):
        return {e: statistics.mean(1.0 if pred(d[(e, s)]) else 0.0 for s in seeds if (e, s) in d) for e in eqs}

    def rec(th):
        return lambda r: as_r2(r["r2"]) is not None and r["status"] == "ok" and as_r2(r["r2"]) >= th

    metrics = {
        "primary": (f"recovery_r2>={args.threshold}", rec(args.threshold)),
        "strict": (f"recovery_r2>={args.strict_threshold}", rec(args.strict_threshold)),
        "catastrophic": (f"catastrophic_r2<{args.catastrophic_r2}",
                         lambda r: as_r2(r["r2"]) is not None and as_r2(r["r2"]) < args.catastrophic_r2),
    }
    rng = random.Random(args.bootstrap_seed)
    comps = [c for c in COMPONENTS if c in idx]
    results = {c: {} for c in comps}
    for tag, (label, pred) in metrics.items():
        pf = per_eq(full, pred)
        for c in comps:
            pa = per_eq(idx[c], pred)
            # effect of REMOVING the component: ablated minus full (negative => component helps)
            diffs = [pa[e] - pf[e] for e in eqs]
            boots = sorted(
                sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs)
                for _ in range(args.bootstrap_iters))
            lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]
            abl_better = sum(1 for d in diffs if d > 0)
            full_better = sum(1 for d in diffs if d < 0)
            results[c][tag] = {
                "metric": label, "full_rate": statistics.mean(pf.values()), "ablated_rate": statistics.mean(pa.values()),
                "ablated_minus_full": statistics.mean(diffs), "bootstrap_95ci": [lo, hi],
                "equations_full_better": full_better, "equations_ablated_better": abl_better,
                "equations_tied": len(eqs) - full_better - abl_better,
                "sign_p": exact_sign_p(full_better, abl_better),
            }
    # Holm across components on the PRIMARY metric only (confirmatory family).
    adj = holm([results[c]["primary"]["sign_p"] for c in comps])
    for c, p in zip(comps, adj):
        r = results[c]["primary"]
        r["sign_p_holm"] = p
        if r["bootstrap_95ci"][1] < 0 and p < args.alpha:
            verdict = "helps"
        elif r["bootstrap_95ci"][0] > 0 and p < args.alpha:
            verdict = "hurts"
        else:
            verdict = "no detectable effect"
        results[c]["verdict_primary"] = verdict
        rt = [float(idx[c][k]["runtime_s"]) / float(full[k]["runtime_s"]) for k in full if float(full[k]["runtime_s"]) > 0]
        results[c]["runtime_ratio_ablated_over_full_median"] = statistics.median(rt) if rt else None
    return {"n_equations": len(eqs), "seeds": seeds, "components": results}


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--phase2-manifest", default=None)
    ap.add_argument("--require-phase2", action="store_true", help="make the Phase 2 tie-in blocking")
    ap.add_argument("--omit", action="append", default=[], metavar="NAME:REASON",
                    help="declare a component not run, with the reason (repeatable)")
    ap.add_argument("--out-dir", default="phase3_out")
    ap.add_argument("--min-seeds", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=0.99)
    ap.add_argument("--strict-threshold", type=float, default=0.999999)
    ap.add_argument("--catastrophic-r2", type=float, default=-10.0)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--reproduce-tol", type=float, default=0.02)
    ap.add_argument("--allow-bypass", action="store_true")
    ap.add_argument("--bootstrap-iters", type=int, default=5000)
    ap.add_argument("--bootstrap-seed", type=int, default=0)
    args = ap.parse_args()

    omitted = {}
    for o in args.omit:
        name, _, reason = o.partition(":")
        if name not in COMPONENTS or not reason.strip():
            print(f"ERROR: --omit needs NAME:REASON with NAME in {COMPONENTS}: {o!r}", file=sys.stderr)
            return 2
        omitted[name] = reason.strip()

    files = expand(args.results)
    try:
        recs = load_records(files)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR reading inputs: {e}", file=sys.stderr)
        return 2
    if not recs:
        print("ERROR: no records loaded", file=sys.stderr)
        return 2

    rep = Report()
    idx = run_checks(recs, args, omitted, rep)
    summary = analyse(idx, args) if idx is not None and rep.closed else None

    os.makedirs(args.out_dir, exist_ok=True)
    manifest = {
        "phase": "Option 3 / Phase 3 - leave-one-gate-out ablation",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "closed": rep.closed,
        "settings": {k: v for k, v in vars(args).items() if k != "results"},
        "omitted_components": omitted,
        "inputs": {f: sha256(f) for f in files if os.path.isfile(f)},
        "checks": rep.checks,
        "analysis": summary,
        "note": ("Primary metric is confirmatory (Holm-adjusted across components). Strict-threshold and "
                 "catastrophic-rate results are exploratory. Effect = ablated minus full; negative means the "
                 "component helps. Omitted components are untested, not shown to be irrelevant."),
    }
    man_path = os.path.join(args.out_dir, "phase3_closure.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    marker = os.path.join(args.out_dir, "PHASE3_CLOSED")
    if os.path.exists(marker):
        os.remove(marker)

    print(f"{'PASS' if rep.closed else 'FAIL'}  checks ({sum(c['passed'] for c in rep.checks)}/{len(rep.checks)} passed)")
    for c in rep.checks:
        if not c["passed"]:
            print(f"  FAIL{' (blocking)' if c['blocking'] else ''}: {c['name']} - {c['detail']}")
    if rep.closed and summary:
        csv_path = os.path.join(args.out_dir, "phase3_components.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["component", "full_rate", "ablated_rate", "ablated_minus_full", "ci_lo", "ci_hi",
                        "sign_p", "sign_p_holm", "verdict", "strict_diff", "catastrophic_diff", "runtime_ratio"])
            for c, r in summary["components"].items():
                p = r["primary"]
                w.writerow([c, f"{p['full_rate']:.4f}", f"{p['ablated_rate']:.4f}", f"{p['ablated_minus_full']:+.4f}",
                            f"{p['bootstrap_95ci'][0]:+.4f}", f"{p['bootstrap_95ci'][1]:+.4f}", f"{p['sign_p']:.4f}",
                            f"{p['sign_p_holm']:.4f}", r["verdict_primary"], f"{r['strict']['ablated_minus_full']:+.4f}",
                            f"{r['catastrophic']['ablated_minus_full']:+.4f}",
                            f"{r['runtime_ratio_ablated_over_full_median']:.2f}"])
        print(f"\nLeave-one-out vs full, n={summary['n_equations']} equations, seeds={summary['seeds']} "
              f"(effect = ablated minus full; negative => component helps)")
        for c, r in summary["components"].items():
            p = r["primary"]
            print(f"  {c:20s} {p['full_rate']:.3f} -> {p['ablated_rate']:.3f}  {p['ablated_minus_full']:+.3f} "
                  f"CI [{p['bootstrap_95ci'][0]:+.3f}, {p['bootstrap_95ci'][1]:+.3f}]  Holm p={p['sign_p_holm']:.3f}  "
                  f"=> {r['verdict_primary']}")
        for n, why in omitted.items():
            print(f"  {n:20s} NOT RUN: {why}")
        with open(marker, "w") as f:
            f.write(f"Phase 3 closed {manifest['generated_utc']}\nmanifest: {man_path}\n")
        print(f"\nPhase 3 CLOSED -> {marker}\nTable: {csv_path}")
    else:
        print("\nPhase 3 NOT closed. Fix the failing blocking checks and rerun.")
    print(f"Manifest: {man_path}")
    return 0 if rep.closed else 1


if __name__ == "__main__":
    sys.exit(main())
