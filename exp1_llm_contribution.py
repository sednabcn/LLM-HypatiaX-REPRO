#!/usr/bin/env python3
"""
Pairwise tests across the three Exp1 arms, read from the checkpoint:
  H = hypatia (LLM on), N = hypatia_nollm, P = pysr_only

  H vs P : total HypatiaX effect
  N vs P : effect of the non-LLM pipeline (FIX-D, FIX-POW, retries, y-scale)
  H vs N : effect of the LLM alone

Usage:  python exp1_llm_contribution.py [checkpoint.json]
Writes: exp1_llm_contribution.json (matched by the exp1_*.json gitignore rule)
"""
import json, sys, math, pathlib
import numpy as np
from scipy import stats

CKPT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "exp1_ablation_checkpoint.json")
TIE_TOL = 1e-2   # same as run_rf01
ARMS = {"P": "pysr_only", "H": "hypatia", "N": "hypatia_nollm"}


def far_r2(d):
    """Find far-OOD R2 in a condition entry. Fails loudly if the key is unknown."""
    if not isinstance(d, dict):
        return None
    for k in ("extrap_r2_far", "far_r2", "extrap_far_r2", "r2_far", "far_ood_r2", "extrap_far", "far"):
        if k in d and isinstance(d[k], (int, float)):
            return float(d[k])
    for outer in ("extrap", "extrapolation", "extrap_r2"):
        if isinstance(d.get(outer), dict) and isinstance(d[outer].get("far"), (int, float)):
            return float(d[outer]["far"])
    return None


def main():
    data = json.loads(CKPT.read_text())
    # tolerate a wrapper dict such as {"results": {...}}
    if "results" in data and isinstance(data["results"], dict):
        data = data["results"]

    rows = {}
    for eq, res in data.items():
        if not isinstance(res, dict):
            continue
        vals = {a: far_r2(res.get(c)) for a, c in ARMS.items()}
        if all(v is not None and math.isfinite(v) for v in vals.values()):
            rows[eq] = vals

    if not rows:
        sample = next((v for v in data.values() if isinstance(v, dict)), {})
        cond = next((v for v in sample.values() if isinstance(v, dict)), {})
        sys.exit("No equation has all three arms with a far-R2 value.\n"
                 f"Keys in one condition entry: {sorted(cond)}\n"
                 "Add the right key name to far_r2() and rerun.")

    P = np.array([r["P"] for r in rows.values()])
    H = np.array([r["H"] for r in rows.values()])
    N = np.array([r["N"] for r in rows.values()])
    print(f"n (equations with all 3 arms) = {len(rows)}: {list(rows)}\n")

    out = {"n": len(rows), "equations": list(rows), "tests": {}}
    for label, a, b in (("H_vs_P", H, P), ("N_vs_P", N, P), ("H_vs_N", H, N)):
        d = a - b
        wins = int((d > TIE_TOL).sum()); losses = int((d < -TIE_TOL).sum())
        ties = len(d) - wins - losses
        tied = np.abs(d) <= TIE_TOL
        a_adj = np.where(tied, b, a)   # collapse within-tolerance pairs into exact ties
        d_adj = np.where(tied, 0.0, d)
        u = stats.mannwhitneyu(a_adj, b, alternative="greater")
        u2 = stats.mannwhitneyu(a_adj, b, alternative="two-sided")
        rbc = 2 * u.statistic / (len(a) * len(b)) - 1
        t = {"median_a": float(np.median(a)), "median_b": float(np.median(b)),
             "wins_ties_losses": [wins, ties, losses],
             "mwu_U": float(u.statistic), "mwu_p_greater": float(u.pvalue),
             "mwu_p_two_sided": float(u2.pvalue), "rank_biserial": float(rbc)}
        t["n_tied"] = int(tied.sum()); t["tie_tol"] = TIE_TOL
        if np.any(d_adj != 0):
            w = stats.wilcoxon(d_adj, alternative="greater", zero_method="wilcox")
            t["wilcoxon_W"] = float(w.statistic); t["wilcoxon_p_greater"] = float(w.pvalue)
        else:
            t["wilcoxon_note"] = "all paired differences within tolerance (all ties)"
        out["tests"][label] = t
        print(f"{label}: median {t['median_a']:+.4f} vs {t['median_b']:+.4f} | "
              f"W/T/L {wins}/{ties}/{losses} | MWU U={u.statistic:.1f} p(>)={u.pvalue:.4f} "
              f"| rank-biserial {rbc:+.3f} | "
              f"Wilcoxon p(>)={t.get('wilcoxon_p_greater', float('nan')):.4f}")

    print("\nNote: with small n these tests have little power; report effect sizes and"
          " W/T/L alongside p-values. Median is used instead of mean because far-R2"
          " has large negative outliers.")
    pathlib.Path("exp1_llm_contribution.json").write_text(json.dumps(out, indent=2))
    print("-> exp1_llm_contribution.json")


if __name__ == "__main__":
    main()
