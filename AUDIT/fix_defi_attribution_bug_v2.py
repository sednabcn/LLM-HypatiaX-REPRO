#!/usr/bin/env python3
"""
fix_defi_attribution_bug_v2.py  (FIX-D2)

Supersedes fix_defi_attribution_bug.py (FIX-D1), which:
  1. Never computed Mean R2 at all (only pass/fail success rates) — but the
     unresolved gap in the paper (Mean R2 = +0.8721, never recomputed after
     the attribution-bug fix) is specifically about Mean R2.
  2. Used the wrong correction rule: named sub-method's raw test_r2 > 0.9,
     rather than the paper's own stated rule (§hybrid-attribution-bug):
     hybrid.test_r2 > 0.99 AND the named sub-method's own success FLAG is
     True. FIX-D1's docstring claimed its 0.9 threshold was "the only
     threshold that reproduces the paper's disclosed LLM-baseline figure of
     62.2% (46/74)" — this does not hold under direct execution: the actual
     LLM-baseline rate at threshold 0.9 is 45/74 = 60.8%, and no threshold
     yields 46/74 for the LLM baseline on either candidate seed42 file.

FIX-D2 (this script) does both jobs correctly, in one place, across all 5
seeds (42, 99, 123, 777, 2024):

  THE PAPER'S ACTUAL CORRECTION RULE (§hybrid-attribution-bug)
  --------------------------------------------------------------
  A task is only a genuine hybrid success if:
      hybrid.test_r2 > 0.99  AND  <named submethod>.success is True
  ("named submethod" = the one hybrid.decision points to: pure_llm for
  decision=="llm"; neural_network for decision in {"nn","nn_fallback"}.)

  A task where hybrid.test_r2 > 0.99 but the named sub-method's success
  flag is NOT True is a fabricated/masked success: the attribution bug
  let a routing artifact report a near-perfect hybrid.test_r2 despite the
  method actually responsible for the answer having failed.

  METRICS COMPUTED PER SEED
  --------------------------------------------------------------
  (a) corrected_success_rate — fraction of the 74 tasks that are genuine
      successes under the rule above.
  (b) llm_baseline_success_rate — fraction of tasks where pure_llm's own
      success flag is True (method-agnostic baseline, unaffected by the
      attribution bug).
  (c) mean_r2_raw — mean of hybrid.test_r2, clipped to [-10, 1], over the
      fixed denominator of 74 (paper's stated Mean R2 methodology).
  (d) mean_r2_corrected — same, but for every fabricated-success task,
      substitutes the named sub-method's OWN test_r2 (NaN/crashed -> -10
      floor) in place of the fabricated hybrid.test_r2, before clipping
      and averaging.

Usage (single seed, matches FIX-D1's CLI for drop-in compatibility):
    python3 fix_defi_attribution_bug_v2.py \
        --input hypatiax_defi_benchmark_v3_results_seed42.json \
        --output defi/hypatix_defi_benchmark_v3c_corrected_seed42.json

Usage (all 5 seeds from a repo checkout — the mode the CI workflow uses):
    python3 fix_defi_attribution_bug_v2.py \
        --repo /path/to/LLM-HypatiaX-REPRO \
        --output-dir /path/to/output_dir \
        --show-tasks
"""

import argparse
import json
import math
import os
from pathlib import Path

SEEDS = [42, 99, 123, 777, 2024]
DENOMINATOR = 74  # fixed, per paper
HYBRID_R2_THRESHOLD = 0.99  # paper's actual threshold (NOT 0.9 — see FIX-D1 note above)

# [FIX-D2-PCA-SOURCE] These were originally hardcoded to the non-PCA "15"
# directory. That directory is real and complete, but it is NOT what
# tab:main_results is built from: the table's OTHER printed figure on the
# same row (90.5% pass rate) matches noise-noiseless/15_pca's
# exp1b_pca_summary.json exactly (335/370 = 0.905405...), and does not match
# any aggregation of the non-PCA "15" files. Default changed to the PCA
# directory accordingly. --seed-dir / --filename-pattern below let the
# caller override either without editing this file, so the non-PCA set
# (still useful as a contrast case) stays one flag away.
RESULTS_SUBDIR = "hypatiax/data/results/comparison_results/noise-noiseless/15_pca"
FILENAME_TEMPLATE = "hypatiax_defi_benchmark_pca_results_seed{seed}.json"

DECISION_TO_SUBMETHOD = {
    "llm": "pure_llm",
    "nn": "neural_network",
    "nn_fallback": "neural_network",
}


def clip(v):
    """Clip to [-10, 1]; treat None/NaN as the -10 catastrophic floor,
    matching the paper's convention that crashed/missing evaluations
    are failures, not R2 scores of zero."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return -10.0
    return max(-10.0, min(float(v), 1.0))


def is_success_flag(sub):
    """True iff the sub-method dict's own 'success' field is exactly True."""
    return sub.get("success") is True


def load(path):
    with open(path) as f:
        return json.load(f)


def named_submethod(rec):
    """Return (name, dict) of the sub-method hybrid.decision points to."""
    decision = rec["results"]["hybrid"].get("decision")
    sub_key = DECISION_TO_SUBMETHOD.get(decision)
    if sub_key is None:
        return decision, {}
    return sub_key, rec["results"].get(sub_key, {})


def correct_task(rec):
    hybrid = rec["results"]["hybrid"]
    decision = hybrid.get("decision")
    hybrid_r2 = hybrid.get("test_r2")

    sub_name, sub = named_submethod(rec)
    sub_r2 = sub.get("test_r2")
    sub_success = sub.get("success")

    llm = rec["results"].get("pure_llm", {})
    llm_success = llm.get("success") is True

    hybrid_claims_near_perfect = (hybrid_r2 is not None) and (hybrid_r2 > HYBRID_R2_THRESHOLD)
    corrected_success = hybrid_claims_near_perfect and is_success_flag(sub)
    fabricated = hybrid_claims_near_perfect and not is_success_flag(sub)

    return {
        "equation_id": rec.get("equation_id"),
        "difficulty": rec.get("difficulty"),
        "decision": decision,
        "hybrid_test_r2": hybrid_r2,
        "submethod": sub_name,
        "submethod_test_r2": sub_r2,
        "submethod_success_flag": sub_success,
        "llm_success_flag": llm_success,
        "corrected_success": corrected_success,
        "fabricated": fabricated,
        "raw_r2_clipped": clip(hybrid_r2),
        "corrected_r2_clipped": clip(sub_r2) if fabricated else clip(hybrid_r2),
    }


def score_file(path):
    data = load(path)
    n = len(data)
    if n != DENOMINATOR:
        print(f"  [warn] {os.path.basename(path)} has {n} tasks, expected {DENOMINATOR}")

    per_task = [correct_task(rec) for rec in data]

    n_corrected_success = sum(1 for t in per_task if t["corrected_success"])
    n_llm_success = sum(1 for t in per_task if t["llm_success_flag"])
    n_fabricated = sum(1 for t in per_task if t["fabricated"])

    mean_r2_raw = sum(t["raw_r2_clipped"] for t in per_task) / DENOMINATOR
    mean_r2_corrected = sum(t["corrected_r2_clipped"] for t in per_task) / DENOMINATOR

    return {
        "n": n,
        "corrected_success_rate": n_corrected_success / DENOMINATOR,
        "llm_baseline_success_rate": n_llm_success / DENOMINATOR,
        "fabricated_count": n_fabricated,
        "mean_r2_raw": mean_r2_raw,
        "mean_r2_corrected": mean_r2_corrected,
        "per_task": per_task,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="Single result JSON (FIX-D1-compatible single-file mode)")
    ap.add_argument("--output", help="Output path for single-file mode")
    ap.add_argument("--repo", help="Path to LLM-HypatiaX-REPRO checkout (5-seed mode)")
    ap.add_argument("--output-dir", help="Directory to write per-seed + summary JSON (5-seed mode)")
    ap.add_argument("--seed", type=int, default=None, help="Only score a single seed (5-seed mode)")
    ap.add_argument("--show-tasks", action="store_true", help="Print fabricated-success task list per seed")
    ap.add_argument("--seed-dir", default=RESULTS_SUBDIR,
                     help=f"Repo-relative dir holding the 5 seed files (default: {RESULTS_SUBDIR}, "
                          "the PCA split — see [FIX-D2-PCA-SOURCE] above). Pass the non-PCA "
                          "'noise-noiseless/15' dir here for the contrast case.")
    ap.add_argument("--filename-pattern", default=FILENAME_TEMPLATE.replace("{seed}", "%s"),
                     help=f"printf-style filename pattern, %s = seed (default matches --seed-dir's "
                          f"split: {FILENAME_TEMPLATE.replace('{seed}', '%s')}). Must be changed "
                          "together with --seed-dir when switching splits -- the two directories "
                          "use different filename conventions (pca_results vs v3_results).")
    args = ap.parse_args()

    # Resolve the two into the same {seed}-format template the rest of the
    # script already uses, so score_file()'s path-building logic is unchanged.
    seed_dir = args.seed_dir
    filename_template = args.filename_pattern.replace("%s", "{seed}")

    if args.input:
        # ── Single-file mode (drop-in FIX-D1 CLI compatibility) ──────────────
        if not args.output:
            ap.error("--output is required with --input")
        r = score_file(args.input)
        out = {
            "benchmark": "hypatix_defi_benchmark_v3c_corrected_v2",
            "correction": (
                "FIX-D2: hybrid-attribution-bug -- success redefined as "
                f"hybrid.test_r2 > {HYBRID_R2_THRESHOLD} AND named sub-method's own "
                "success flag is True (paper's actual §hybrid-attribution-bug rule, "
                "not the 0.9-numeric-threshold rule used by the retracted FIX-D1 script). "
                "Mean R2 (raw + attribution-corrected) is now computed in the same pass."
            ),
            "source_file": Path(args.input).name,
            "summary": {k: v for k, v in r.items() if k != "per_task"},
            "per_task": r["per_task"],
        }
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2))
        print(f"Wrote {out_path}")
        print(json.dumps(out["summary"], indent=2))
        return

    if not args.repo:
        ap.error("either --input or --repo is required")

    # ── 5-seed mode ──────────────────────────────────────────────────────────
    seeds = [args.seed] if args.seed else SEEDS
    out_dir = Path(args.output_dir) if args.output_dir else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    for seed in seeds:
        path = os.path.join(args.repo, seed_dir, filename_template.format(seed=seed))
        if not os.path.exists(path):
            print(f"seed {seed}: file not found at {path}, skipping")
            continue
        r = score_file(path)
        all_results[seed] = r
        print(
            f"seed {seed}: n={r['n']}  "
            f"corrected_success={r['corrected_success_rate']:.4f}  "
            f"llm_baseline={r['llm_baseline_success_rate']:.4f}  "
            f"raw_mean_R2={r['mean_r2_raw']:.4f}  "
            f"corrected_mean_R2={r['mean_r2_corrected']:.4f}  "
            f"fabricated={r['fabricated_count']}"
        )
        if args.show_tasks:
            for t in r["per_task"]:
                if t["fabricated"]:
                    print(
                        f"    - {t['equation_id']} ({t['difficulty']}): "
                        f"hybrid={t['hybrid_test_r2']:.4f} via {t['decision']}, "
                        f"{t['submethod']}.test_r2={t['submethod_test_r2']} "
                        f"success_flag={t['submethod_success_flag']}"
                    )
        # per-seed detail file
        seed_out = out_dir / f"fix_defi_attribution_v2_seed{seed}.json"
        seed_out.write_text(json.dumps(r, indent=2))

    if not all_results:
        print("No seed files found — nothing scored.")
        return 1

    n = len(all_results)
    summary = {
        "correction": (
            f"FIX-D2: hybrid.test_r2 > {HYBRID_R2_THRESHOLD} AND named sub-method "
            "success flag True (paper's actual rule)"
        ),
        "seeds_scored": sorted(all_results.keys()),
        "per_seed": {
            str(seed): {k: v for k, v in r.items() if k != "per_task"}
            for seed, r in all_results.items()
        },
        "avg_corrected_success_rate": sum(r["corrected_success_rate"] for r in all_results.values()) / n,
        "avg_llm_baseline_success_rate": sum(r["llm_baseline_success_rate"] for r in all_results.values()) / n,
        "avg_mean_r2_raw": sum(r["mean_r2_raw"] for r in all_results.values()) / n,
        "avg_mean_r2_corrected": sum(r["mean_r2_corrected"] for r in all_results.values()) / n,
    }
    summary_path = out_dir / "fix_defi_attribution_v2_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print()
    print(f"5-seed average: corrected_success={summary['avg_corrected_success_rate']:.4f}  "
          f"llm_baseline={summary['avg_llm_baseline_success_rate']:.4f}  "
          f"raw_mean_R2={summary['avg_mean_r2_raw']:.4f}  "
          f"corrected_mean_R2={summary['avg_mean_r2_corrected']:.4f}")
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
