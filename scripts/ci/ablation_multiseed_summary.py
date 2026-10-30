#!/usr/bin/env python3
"""Summarise exp1_ablation across repeat seeds.

Reads exp1_ablation_results.json from the canonical (seed 42) dir and from each
ablation/exp1_ablation_seed<N> dir, then reports per equation the far-extrapolation R^2 of the
three arms for every seed, the per-equation median over seeds, how often each arm reaches
R^2 >= 0.99, and paired tests on the per-equation medians (the equation, not the seed, is the
unit: seeds of one equation are not independent).

usage: ablation_multiseed_summary.py [--root hypatiax/data/results/ablation] [--out summary.json]
"""
import argparse, glob, json, math, os, re, statistics as st

ARMS = ("pysr_only", "hypatia", "hypatia_nollm")
TOL = 0.01


def load(root):
    runs = {}
    for d in sorted(glob.glob(os.path.join(root, "exp1_ablation*"))):
        m = re.search(r"exp1_ablation(?:_seed(\d+))?$", d)
        f = os.path.join(d, "exp1_ablation_results.json")
        if m and os.path.isfile(f):
            runs[int(m.group(1) or 42)] = json.load(open(f))
    return runs


def _holm(pvals):
    """Holm-Bonferroni step-down adjusted p-values (same order as input; None stays None)."""
    idx = [i for i, p in enumerate(pvals) if p is not None]
    order = sorted(idx, key=lambda i: pvals[i])
    adj, run, m = [None] * len(pvals), 0.0, len(order)
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvals[i]))
        adj[i] = run
    return adj


def far(row, arm):
    v = (row.get(arm) or {}).get("extrap_r2_far")
    return -math.inf if v is None else float(v)


def med(xs):
    """Median that tolerates -inf (statistics.median averages the middle pair)."""
    return st.median(xs)


def wtl(a, b):
    w = sum(x - y > TOL for x, y in zip(a, b)); l = sum(y - x > TOL for x, y in zip(a, b))
    return w, len(a) - w - l, l


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="hypatiax/data/results/ablation")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    runs = load(a.root)
    seeds = sorted(runs)
    if len(seeds) < 2:
        raise SystemExit(f"need >=2 seed dirs under {a.root}, found {seeds}")
    ids = sorted(set.intersection(*[set(r) for r in runs.values()]), key=int)
    per = {}
    for k in ids:
        name = runs[seeds[0]][k]["name"]
        per[name] = {arm: {s: far(runs[s][k], arm) for s in seeds} for arm in ARMS}

    f = lambda v: "-inf" if v == -math.inf else f"{v:.4f}"
    print(f"seeds: {seeds}   equations: {len(per)}\n")
    print(f"{'equation':24s} " + "  ".join(f"{arm[:9]:>9s}(med  min..max)" for arm in ARMS))
    for name, d in per.items():
        cells = []
        for arm in ARMS:
            v = list(d[arm].values())
            cells.append(f"{f(med(v)):>9s} ({f(min(v))}..{f(max(v))})")
        print(f"{name[:24]:24s} " + "  ".join(cells))

    n_cells = len(per) * len(seeds)
    fails = {arm: sum(not math.isfinite(v) for d in per.values() for v in d[arm].values()) for arm in ARMS}
    print("failed cells (no finite far R2, of %d): " % n_cells + ", ".join(f"{k}={v}" for k, v in fails.items()))
    rec = {arm: sum(v >= 0.99 for d in per.values() for v in d[arm].values()) for arm in ARMS}
    print("\nfar R2 >= 0.99 (equation x seed cells, of %d): " % n_cells + ", ".join(f"{k}={v}" for k, v in rec.items()))

    meds = {name: {arm: med(list(d[arm].values())) for arm in ARMS} for name, d in per.items()}
    usable = [n for n, m in meds.items() if all(math.isfinite(m[arm]) for arm in ARMS)]
    print(f"\npaired on per-equation medians, n={len(usable)} (excluded: {sorted(set(per) - set(usable)) or 'none'})")
    out = {"seeds": seeds, "n_equations": len(per), "recovered_ge_0.99": rec, "failed_cells": fails,
           "excluded_from_paired": sorted(set(per) - set(usable)),
           "primary_test": "wilcoxon_signed_rank", "multiplicity": "holm_across_3_comparisons", "paired": {}}
    try:
        from scipy.stats import mannwhitneyu, wilcoxon
    except Exception:
        mannwhitneyu = wilcoxon = None
    for label, x, y in (("hypatia_vs_pysr", "hypatia", "pysr_only"), ("hypatia_vs_nollm", "hypatia", "hypatia_nollm"),
                        ("nollm_vs_pysr", "hypatia_nollm", "pysr_only")):
        A = [meds[n][x] for n in usable]; B = [meds[n][y] for n in usable]
        w, t, l = wtl(A, B)
        rec_ = {"wins": w, "ties": t, "losses": l}
        if wilcoxon and len(A) >= 3:
            # PRIMARY: paired Wilcoxon on within-tolerance-collapsed differences (|d|<=TOL -> tie)
            d = [0.0 if abs(p - q) <= TOL else p - q for p, q in zip(A, B)]
            if any(x != 0 for x in d):
                rec_["wilcoxon_p_greater"] = float(wilcoxon(d, alternative="greater", zero_method="wilcox").pvalue)
                rec_["wilcoxon_p_two_sided"] = float(wilcoxon(d, alternative="two-sided", zero_method="wilcox").pvalue)
            # SENSITIVITY ONLY: unpaired test ignores the pairing
            rec_["mwu_sensitivity_p_greater"] = float(mannwhitneyu(A, B, alternative="greater").pvalue)  # audit: ignore[S1] sensitivity check only; primary test is paired Wilcoxon + Holm
            rec_["mwu_sensitivity_p_two_sided"] = float(mannwhitneyu(A, B, alternative="two-sided").pvalue)  # audit: ignore[S1] sensitivity check only; primary test is paired Wilcoxon + Holm
        out["paired"][label] = rec_
    _labs = list(out["paired"])
    _adj = _holm([out["paired"][l].get("wilcoxon_p_greater") for l in _labs])
    for l, ap in zip(_labs, _adj):
        out["paired"][l]["wilcoxon_p_greater_holm"] = ap
        r_ = out["paired"][l]
        print(f"  {l:18s} W/T/L {r_['wins']}/{r_['ties']}/{r_['losses']}  PRIMARY wilcoxon p(>)={r_.get('wilcoxon_p_greater')} "
              f"holm={ap}  | sensitivity: " + "  ".join(f"{k}={v:.3f}" for k, v in r_.items() if k.startswith("mwu")))
    # per-seed W/T/L (stability of the headline count)
    print("\nper-seed W/T/L (hypatia vs pysr_only | hypatia vs nollm), ties within %.2f:" % TOL)
    for s in seeds:
        names = list(per)
        A = [per[n]["hypatia"][s] for n in names]
        row = [wtl(A, [per[n][arm][s] for n in names]) for arm in ("pysr_only", "hypatia_nollm")]
        out.setdefault("per_seed", {})[s] = {"vs_pysr": row[0], "vs_nollm": row[1]}
        print(f"  seed {s:>5d}: {row[0]} | {row[1]}")
    if a.out:
        json.dump(out, open(a.out, "w"), indent=2); print("\nwrote", a.out)


if __name__ == "__main__":
    main()
