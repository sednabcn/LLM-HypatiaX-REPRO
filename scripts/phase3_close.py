#!/usr/bin/env python3
"""
phase3_close.py - closure gate for Option 3 / Phase 3 (leave-one-gate-out ablation).

Takes per-case results for the full HDS v50_2 configuration and for each
leave-one-out configuration, verifies the ablation is controlled, and reports each
component's measured contribution. Writes:

    phase3_closure.json     checks, per-component results, input hashes, analysis plan
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
    equation, seed, split_id, r2, r2_raw, r2_status, status, formula, generation_path,
    llm_called, bypass_used, runtime_s, timeout_s, model_id, code_version,
    evaluator_version, git_commit, code_dirty, evaluator_sha256, prompt_template_sha256,
    train_data_sha256, far_data_sha256
Optional: extrap_r2_far (must equal r2 if present), error_stage, candidate_r2_status.

What this version adds over the first one (each item closes a gap found in Phase 2):
    G1  data parity      train/far data hashes identical across configurations per
                         (equation, seed), and optionally against the P-arm rows (--p-rows)
    G2  score parity     r2 == r2_raw (== extrap_r2_far if logged) on every ok row; failed
                         rows cannot carry a recovered score
    G3  live LLM         llm_called must be a bool and True (except --llm-optional components)
    G4  prompt/timeout   one prompt_template_sha256 and one timeout_s across all rows
    G8  clean tree       code_dirty False, git_commit single, no "+dirty" code_version
                         (--allow-dirty downgrades to a recorded caveat)
    evaluator pin        one evaluator_sha256 (optionally a prefix via --expected-evaluator-sha)
    no_calls relabel     rows labelled no_calls that have live, all non-finite candidates are
                         reported as "failed: all candidates non-finite" (they stay failures);
                         genuine no_calls rows (no live call) block closure until rerun
    fixed analysis plan  primary metric, interval method, test and multiplicity are declared
                         below and checked against the CLI settings before any result is read
    power note           minimum number of non-tied equations a Holm-adjusted sign test can
                         ever call significant; components below it are flagged underpowered
    non-finite scoring   NaN/inf/failed rows count as NOT recovered and as catastrophic

Usage:
    python phase3_close.py --results results/ablation/*.jsonl \
        --phase2-manifest phase2_out/phase2_closure.json --out-dir phase3_out \
        --expected-evaluator-sha 7d5395ed --p-rows "p2/pure_llm_seed*.jsonl"
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
            "r2_raw", "r2_status", "status", "formula", "generation_path", "llm_called",
            "bypass_used", "runtime_s", "timeout_s", "model_id", "code_version",
            "evaluator_version", "git_commit", "code_dirty", "evaluator_sha256",
            "prompt_template_sha256", "train_data_sha256", "far_data_sha256"]
NULLABLE = {"ablated_component", "r2", "r2_raw", "formula"}
NUMERIC = ("r2", "r2_raw", "runtime_s", "timeout_s")
OK_R2_STATUS = {"ok"}

# Declared BEFORE launching the runs (Section 6 style). The CLI must match, or the run is
# labelled exploratory. Changing this block after seeing results is a protocol deviation.
ANALYSIS_PLAN = {
    "primary_metric": "recovery_r2>=0.99 per equation, mean over seeds; failed, timed-out, "
                      "non-finite and NaN rows count as NOT recovered",
    "effect": "ablated minus full (negative => component helps)",
    "interval": "percentile bootstrap over equations, 5000 resamples, seed 0, 95%",
    "test": "exact two-sided sign test over equations, ties dropped",
    "multiplicity": "Holm across components, primary metric only (confirmatory)",
    "alpha": 0.05,
    "exploratory": "strict-threshold and catastrophic-rate results",
    "power_note": "With 15 equations a sign test has little power: see min_nontied_equations.",
}
PLAN_ARGS = {"threshold": 0.99, "alpha": 0.05, "bootstrap_iters": 5000, "bootstrap_seed": 0}


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
    """float, +-inf kept (non-finite is a failure, not a missing value); None for NaN/unparseable."""
    if v is None:
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def finite(v):
    return v is not None and math.isfinite(v)


def comp_of(r):
    c = r.get("ablated_component")
    return "full" if c in FULL_LABELS else str(c)


def _stage_text(r):
    return f"{r.get('status')} {r.get('r2_status')} {r.get('error_stage')}"


def mislabelled_nocalls(r):
    """no_calls label, but live call(s) were made and every candidate scored non-finite."""
    cands = r.get("candidate_r2_status") or []
    return ("no_calls" in _stage_text(r) and r.get("llm_called") is True and bool(cands)
            and all(c == "nonfinite_pred" for c in cands))


def genuine_nocalls(r):
    return "no_calls" in _stage_text(r) and not mislabelled_nocalls(r)


class Report:
    def __init__(self):
        self.checks = []
        self.caveats = []

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


def min_nontied(alpha, m):
    """Smallest number of non-tied equations at which an all-one-direction sign test can
    reach Holm-level significance (alpha / m for the single best component)."""
    for n in range(1, 200):
        if exact_sign_p(n, 0) <= alpha / max(m, 1):
            return n
    return None


# ------------------------------------------------------------------ checks
def run_checks(recs, args, omitted, rep):
    bad = [f"{r.get('_file','?')}: missing/null '{k}'" for r in recs for k in REQUIRED
           if k not in r or (r[k] is None and k not in NULLABLE)]
    for r in recs:
        for k in NUMERIC:
            if k in r and r[k] is not None:
                try:
                    float(r[k])
                except (TypeError, ValueError):
                    bad.append(f"{r.get('_file','?')}: non-numeric '{k}'={r[k]!r}")
    rep.add("schema complete", not bad, f"{len(bad)} problems; first: {bad[:3]}" if bad else f"{len(recs)} records OK")
    if bad:
        return None

    # Analysis plan fixed before launch.
    dev = {k: (getattr(args, k), v) for k, v in PLAN_ARGS.items() if getattr(args, k) != v}
    rep.add("analysis settings equal the pre-declared plan", not dev,
            f"deviations (got, planned): {dev}" if dev else "matches ANALYSIS_PLAN",
            blocking=not args.exploratory)
    if dev and args.exploratory:
        rep.caveats.append(f"exploratory run, settings deviate from the declared plan: {dev}")

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
        # G1: split_id is derived from equation|seed, so it proves nothing about the data.
        dh = [k for k in full_keys & set(idx[comp])
              if (idx[comp][k]["train_data_sha256"], idx[comp][k]["far_data_sha256"])
              != (idx["full"][k]["train_data_sha256"], idx["full"][k]["far_data_sha256"])]
        rep.add(f"[{comp}] G1 identical train/far data hashes as full", not dh,
                f"{len(dh)} mismatches; first: {dh[:3]}")
        want = [] if comp == "full" else [comp]
        wrong = [k for k, r in idx[comp].items() if sorted(r["config_diff"]) != want]
        rep.add(f"[{comp}] config differs from full ONLY by this component", not wrong,
                f"{len(wrong)} rows with other config changes; first: {wrong[:3]}")
    wrong_full = [k for k, r in idx["full"].items() if list(r["config_diff"]) != []]
    rep.add("[full] config_diff is empty", not wrong_full, f"{len(wrong_full)} rows")

    seeds = sorted({k[1] for k in full_keys})
    rep.add(f"at least {args.min_seeds} seeds", len(seeds) >= args.min_seeds, f"seeds: {seeds}")

    # G4 / evaluator / model: one value everywhere.
    for field in ("model_id", "code_version", "evaluator_version", "timeout_s",
                  "evaluator_sha256", "prompt_template_sha256", "git_commit"):
        vals = sorted({str(r[field]) for r in recs})
        label = {"prompt_template_sha256": "G4 single prompt_template_sha256",
                 "timeout_s": "G4 single timeout_s",
                 "git_commit": "G8 single git_commit"}.get(field, f"single {field}")
        rep.add(f"{label} across all configurations", len(vals) == 1, f"values: {vals[:5]}")
    if args.expected_evaluator_sha:
        evs = {str(r["evaluator_sha256"]) for r in recs}
        rep.add("evaluator_sha256 matches the pinned evaluator",
                all(v.startswith(args.expected_evaluator_sha) for v in evs),
                f"expected prefix {args.expected_evaluator_sha}; found {sorted(evs)[:3]}")
    else:
        rep.add("evaluator pinned (--expected-evaluator-sha)", False,
                "not supplied; evaluator hash is consistent but not tied to r2_canonical.py",
                blocking=False)

    # G8: a clean tree, or a recorded caveat.
    dirty_rows = [(comp_of(r), r["equation"], r["seed"]) for r in recs
                  if r["code_dirty"] is not False or "dirty" in str(r["code_version"]).lower()
                  or "dirty" in str(r["git_commit"]).lower()]
    rep.add("G8 clean working tree (code_dirty False, no +dirty suffix)", not dirty_rows,
            f"{len(dirty_rows)} rows dirty; first: {dirty_rows[:3]}", blocking=not args.allow_dirty)
    if dirty_rows and args.allow_dirty:
        rep.caveats.append(f"{len(dirty_rows)} rows were produced from a dirty tree; exact working-tree "
                           f"state is not recoverable (G8 not met, accepted by --allow-dirty)")

    # G3: live LLM calls.
    nb = [(comp_of(r), r["equation"], r["seed"]) for r in recs if not isinstance(r["llm_called"], bool)]
    rep.add("G3 llm_called is a boolean on every row", not nb, f"{len(nb)} rows; first: {nb[:3]}")
    off = [(comp_of(r), r["equation"], r["seed"]) for r in recs
           if r["llm_called"] is not True and comp_of(r) not in set(args.llm_optional)]
    rep.add("G3 llm_called is True on every row (except --llm-optional components)", not off,
            f"{len(off)} rows with no live call; first: {off[:3]}")

    # G2: score parity.
    s2 = []
    for r in recs:
        a, raw = as_r2(r["r2"]), as_r2(r["r2_raw"])
        key = (comp_of(r), r["equation"], r["seed"])
        if r["status"] == "ok":
            if not (finite(a) and finite(raw) and math.isclose(a, raw, rel_tol=1e-12, abs_tol=1e-12)):
                s2.append(key)
            elif str(r["r2_status"]) not in OK_R2_STATUS:
                s2.append(key)
            elif r.get("extrap_r2_far") is not None:
                e = as_r2(r["extrap_r2_far"])
                if not (finite(e) and math.isclose(a, e, rel_tol=1e-12, abs_tol=1e-12)):
                    s2.append(key)
        elif finite(a) and a >= args.threshold:
            s2.append(key)   # a failed row must not carry a recovered score
    rep.add("G2 r2 == r2_raw (== extrap_r2_far) on ok rows; failed rows carry no recovered score",
            not s2, f"{len(s2)} rows; first: {s2[:3]}")

    # no_calls handling.
    relabel = [(comp_of(r), r["equation"], r["seed"]) for r in recs if mislabelled_nocalls(r)]
    genuine = [(comp_of(r), r["equation"], r["seed"]) for r in recs if genuine_nocalls(r)]
    rep.add("no genuine no_calls rows (infrastructure failures must be rerun)", not genuine,
            f"{len(genuine)} rows; first: {genuine[:3]}")
    rep.add("no_calls rows with live non-finite candidates (reported as failed: non-finite)", True,
            f"{len(relabel)} rows relabelled in the report, counted as failures; first: {relabel[:3]}",
            blocking=False)

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

    # G1 against the P arm, if supplied (HDS exp1 rows carry no data hashes, so this is optional).
    if args.p_rows:
        try:
            prow = {(r["equation"], int(r["seed"])): r for r in load_records(expand(args.p_rows))}
            mm = [k for k, r in idx["full"].items() if k in prow and
                  (r["train_data_sha256"], r["far_data_sha256"]) != (prow[k].get("train_data_sha256"),
                                                                     prow[k].get("far_data_sha256"))]
            nok = [k for k in idx["full"] if k not in prow]
            rep.add("G1 full-config data hashes equal the P-arm rows", not mm and not nok,
                    f"{len(mm)} mismatches {mm[:3]}; {len(nok)} keys absent from P rows {nok[:3]}")
        except (OSError, json.JSONDecodeError) as e:
            rep.add("P-arm rows readable for the G1 comparison", False, str(e))
    else:
        rep.add("G1 comparison with the P arm (--p-rows)", False,
                "not supplied; only ablation-vs-full data parity was checked", blocking=False)

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
                    1.0 if (finite(as_r2(r["r2"])) and r["status"] == "ok" and as_r2(r["r2"]) >= args.threshold) else 0.0
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
        return lambda r: finite(as_r2(r["r2"])) and r["status"] == "ok" and as_r2(r["r2"]) >= th

    def catastrophic(r):
        a = as_r2(r["r2"])
        return r["status"] != "ok" or not finite(a) or a < args.catastrophic_r2

    metrics = {
        "primary": (f"recovery_r2>={args.threshold}", rec(args.threshold)),
        "strict": (f"recovery_r2>={args.strict_threshold}", rec(args.strict_threshold)),
        "catastrophic": (f"catastrophic (failed, non-finite or r2<{args.catastrophic_r2})", catastrophic),
    }
    rng = random.Random(args.bootstrap_seed)
    comps = [c for c in COMPONENTS if c in idx]
    k_min = min_nontied(args.alpha, len(comps))
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
        n_nt = r["equations_full_better"] + r["equations_ablated_better"]
        r["n_nontied"] = n_nt
        r["underpowered"] = k_min is None or n_nt < k_min
        if r["bootstrap_95ci"][1] < 0 and p < args.alpha:
            verdict = "helps"
        elif r["bootstrap_95ci"][0] > 0 and p < args.alpha:
            verdict = "hurts"
        elif r["underpowered"]:
            verdict = "no detectable effect (underpowered)"
        else:
            verdict = "no detectable effect"
        results[c]["verdict_primary"] = verdict
        rt = [float(idx[c][k]["runtime_s"]) / float(full[k]["runtime_s"]) for k in full if float(full[k]["runtime_s"]) > 0]
        results[c]["runtime_ratio_ablated_over_full_median"] = statistics.median(rt) if rt else None
    return {"n_equations": len(eqs), "seeds": seeds, "min_nontied_equations": k_min, "components": results}


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--phase2-manifest", default=None)
    ap.add_argument("--require-phase2", action="store_true", help="make the Phase 2 tie-in blocking")
    ap.add_argument("--p-rows", nargs="+", default=None, help="P-arm jsonl rows for the G1 data-hash comparison")
    ap.add_argument("--expected-evaluator-sha", default=None, help="sha256 prefix of hypatiax/core/r2_canonical.py")
    ap.add_argument("--allow-dirty", action="store_true", help="accept a dirty tree as a recorded caveat (G8)")
    ap.add_argument("--llm-optional", action="append", default=[], metavar="COMPONENT",
                    help="component whose rows may have llm_called False (repeatable)")
    ap.add_argument("--exploratory", action="store_true", help="allow settings that deviate from ANALYSIS_PLAN")
    ap.add_argument("--omit", action="append", default=[], metavar="NAME:REASON",
                    help="declare a component not run, with the reason (repeatable)")
    ap.add_argument("--out-dir", default="phase3_out")
    ap.add_argument("--min-seeds", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=0.99)
    ap.add_argument("--strict-threshold", type=float, default=0.999999)
    ap.add_argument("--catastrophic-r2", type=float, default=-10.0)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--reproduce-tol", type=float, default=0.067)
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

    relabelled = [{"component": comp_of(r), "equation": r["equation"], "seed": r["seed"],
                   "reported_as": "failed: all candidates non-finite"}
                  for r in recs if mislabelled_nocalls(r)]
    os.makedirs(args.out_dir, exist_ok=True)
    inputs = {f: sha256(f) for f in files if os.path.isfile(f)}
    if args.phase2_manifest and os.path.isfile(args.phase2_manifest):
        inputs[args.phase2_manifest] = sha256(args.phase2_manifest)
    manifest = {
        "phase": "Option 3 / Phase 3 - leave-one-gate-out ablation",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "closed": rep.closed,
        "exploratory": bool(args.exploratory),
        "settings": {k: v for k, v in vars(args).items() if k != "results"},
        "analysis_plan": ANALYSIS_PLAN,
        "omitted_components": omitted,
        "caveats": rep.caveats,
        "relabelled_no_calls_rows": relabelled,
        "inputs": inputs,
        "checks": rep.checks,
        "analysis": summary,
        "note": ("Primary metric is confirmatory (Holm-adjusted across components). Strict-threshold and "
                 "catastrophic-rate results are exploratory. Effect = ablated minus full; negative means the "
                 "component helps. Omitted components are untested, not shown to be irrelevant. Components "
                 "flagged underpowered cannot be called significant by a sign test over this few equations."),
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
            print(f"  FAIL{' (blocking)' if c['blocking'] else ' (non-blocking)'}: {c['name']} - {c['detail']}")
    for cav in rep.caveats:
        print(f"  CAVEAT: {cav}")
    if rep.closed and summary:
        csv_path = os.path.join(args.out_dir, "phase3_components.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["component", "full_rate", "ablated_rate", "ablated_minus_full", "ci_lo", "ci_hi",
                        "n_nontied", "underpowered", "sign_p", "sign_p_holm", "verdict", "strict_diff",
                        "catastrophic_diff", "runtime_ratio"])
            for c, r in summary["components"].items():
                p = r["primary"]
                rt = r["runtime_ratio_ablated_over_full_median"]
                w.writerow([c, f"{p['full_rate']:.4f}", f"{p['ablated_rate']:.4f}", f"{p['ablated_minus_full']:+.4f}",
                            f"{p['bootstrap_95ci'][0]:+.4f}", f"{p['bootstrap_95ci'][1]:+.4f}",
                            p["n_nontied"], p["underpowered"], f"{p['sign_p']:.4f}",
                            f"{p['sign_p_holm']:.4f}", r["verdict_primary"], f"{r['strict']['ablated_minus_full']:+.4f}",
                            f"{r['catastrophic']['ablated_minus_full']:+.4f}",
                            "" if rt is None else f"{rt:.2f}"])
        print(f"\nLeave-one-out vs full, n={summary['n_equations']} equations, seeds={summary['seeds']} "
              f"(effect = ablated minus full; negative => component helps)")
        print(f"Power: a Holm-level sign test needs >= {summary['min_nontied_equations']} non-tied equations.")
        for c, r in summary["components"].items():
            p = r["primary"]
            print(f"  {c:20s} {p['full_rate']:.3f} -> {p['ablated_rate']:.3f}  {p['ablated_minus_full']:+.3f} "
                  f"CI [{p['bootstrap_95ci'][0]:+.3f}, {p['bootstrap_95ci'][1]:+.3f}]  "
                  f"non-tied={p['n_nontied']}  Holm p={p['sign_p_holm']:.3f}  => {r['verdict_primary']}")
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
