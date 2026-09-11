#!/usr/bin/env python3
"""
mean_r2_by_seed.py
===================
Compute mean test R² by seed (and by method) from saved HypatiaX DeFi
benchmark result files, WITHOUT importing torch / anthropic / the full
benchmark script. Works against the per-seed output of hypatiax_defi_benchmark_v4.py,
hypatiax_defi_benchmark_pca.py, or hypatiax_defi_benchmark_v4_pca.py:

    hypatiax_defi_benchmark_v4_results_seed42.json
    hypatiax_defi_benchmark_pca_results_seed99.json
    ... etc.

as well as a single-seed / non-swept run's plain output file
(hypatiax_defi_benchmark_*_results.json).

IMPORTANT — same basename, different experiments, different directories:
hypatiax_defi_benchmark_pca.py (exp1_pca / exp1b_pca) and
hypatiax_defi_benchmark_v4_pca.py (exp1c_pca) both write files literally
named hypatiax_defi_benchmark_pca_results_seed<N>.json /
hypatiax_defi_benchmark_pca_pooled_seed_report.json — the script name in
the filename does NOT disambiguate which experiment produced it. The only
thing that does is the containing directory:

    comparison_results/noise-noiseless/noiseless/defi_pca/   exp1_pca   (all 74 cases, single default seed)
    comparison_results/noise-noiseless/15_pca/                exp1b_pca  (v3c/pca portfolio seed sweep)
    comparison_results/noise-noiseless/exp1c_pca/              exp1c_pca  (v4 validation-selected hybrid seed sweep)
    comparison_results/noise-noiseless/exp1c_v4/                exp1c      (non-PCA v4 counterpart of exp1c_pca —
                                                                             hypatiax_defi_benchmark_v4.py; files here
                                                                             are shard/seed-suffixed on the way in by
                                                                             run_all.sh's move step, so they don't hit
                                                                             this same-basename collision, but the dir
                                                                             is listed here so all four DeFi variants —
                                                                             exp1_pca / exp1b_pca / exp1c_pca / exp1c —
                                                                             are in one place)

Point this script at exactly ONE of those directories per invocation. Passing
more than one of them together (e.g. both defi_pca/ and exp1c_pca/) will
silently pool two different experiments' results under the same seed keys —
see the cross-directory basename-collision check in main() below, which
warns (but does not block) when this looks like it may have happened.

Why this exists as a separate script (not just the pooled-seed-report
function inside the benchmark files): the benchmark scripts require
torch + anthropic just to import, which is unnecessary weight for a
read-only aggregation over already-completed results — e.g. auditing a
past CI run's shard outputs, or comparing v4 vs pca side by side,
without spinning up the full benchmark environment.

Each input record is expected to look like:
    {
      "equation_id": "...",
      "seed": 42,                 # may be null for a non-swept run
      "results": {
        "pure_llm":       {"test_r2": ..., ...},
        "neural_network":  {"test_r2": ..., ...},
        "hybrid":          {"test_r2": ..., ...},
        ...
      },
      ...
    }

If a record's "seed" is null/missing, the seed is inferred from the
filename's "_seed<N>" suffix when present; otherwise the record is
grouped under seed key "unspecified".

Usage
-----
  python mean_r2_by_seed.py results/*.json
  python mean_r2_by_seed.py results/                       # scans dir for *.json
  python mean_r2_by_seed.py results/ --glob "hypatiax_defi_benchmark_pca_results*.json"
  python mean_r2_by_seed.py results/ --methods pure_llm hybrid
  python mean_r2_by_seed.py results/ --clip -5 --out summary.json

  # PCA-variant directories — pass exactly one of these per invocation
  # (see the basename-collision note above):
  python mean_r2_by_seed.py hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/
  python mean_r2_by_seed.py hypatiax/data/results/comparison_results/noise-noiseless/15_pca/
  python mean_r2_by_seed.py hypatiax/data/results/comparison_results/noise-noiseless/exp1c_pca/

  # Non-PCA v4 counterpart (exp1c) — filenames are already shard/seed-suffixed
  # here so this one is safe to combine with others if you want a v4-vs-v4_pca
  # comparison:
  python mean_r2_by_seed.py hypatiax/data/results/comparison_results/noise-noiseless/exp1c_v4/
"""

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

_SEED_RE = re.compile(r"_seed(-?\d+)")
_DEFAULT_METHODS = ["pure_llm", "neural_network", "hybrid"]


def _seed_from_filename(path: Path):
    m = _SEED_RE.search(path.name)
    return int(m.group(1)) if m else None


def _collect_files(paths: list[str], glob: str) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            files.extend(sorted(pp.glob(glob)))
        elif pp.is_file():
            files.append(pp)
        else:
            print(f"⚠️  Skipping (not found): {p}", file=sys.stderr)
    # De-dup while preserving order (a dir glob and an explicit path could overlap)
    seen, out = set(), []
    for f in files:
        rp = f.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(f)
    return out


def _warn_cross_experiment_basenames(files: list[Path]) -> None:
    """Warn (non-fatal) when the same filename shows up under more than one
    parent directory among the given files.

    hypatiax_defi_benchmark_pca.py (exp1_pca / exp1b_pca) and
    hypatiax_defi_benchmark_v4_pca.py (exp1c_pca) both write identically
    named hypatiax_defi_benchmark_pca_results_seed<N>.json /
    hypatiax_defi_benchmark_pca_pooled_seed_report.json files, so this is
    the only cheap signal available that a caller may have pointed this
    script at more than one of defi_pca/, 15_pca/, exp1c_pca/ at once,
    which would silently pool two different experiments together.
    """
    by_name: dict = {}
    for f in files:
        by_name.setdefault(f.name, set()).add(str(f.parent.resolve()))

    offenders = {name: dirs for name, dirs in by_name.items() if len(dirs) > 1}
    if offenders:
        print("⚠️  Same filename found in multiple directories — this usually means "
              "results from more than one experiment (e.g. exp1_pca / exp1b_pca / "
              "exp1c_pca) are being pooled together:", file=sys.stderr)
        for name, dirs in sorted(offenders.items()):
            print(f"    {name}:", file=sys.stderr)
            for d in sorted(dirs):
                print(f"        {d}", file=sys.stderr)
        print("    Re-run pointed at a single experiment's directory if this "
              "wasn't intended.", file=sys.stderr)


def _load_records(files: list[Path]) -> list[dict]:
    """Return a flat list of case records, each tagged with a resolved seed
    and its source file (for traceability / debugging)."""
    records = []
    for f in files:
        try:
            data = json.loads(f.read_text())
        except Exception as e:
            print(f"⚠️  Could not parse {f}: {e}", file=sys.stderr)
            continue
        # Accept either a bare list of records, or a dict with a "results"/
        # "tests" list wrapper — be liberal in what we accept since these
        # files have accreted a few schema variants over time.
        if isinstance(data, dict):
            rows = data.get("results") or data.get("tests") or []
            if not isinstance(rows, list):
                rows = []
        elif isinstance(data, list):
            rows = data
        else:
            rows = []

        file_seed = _seed_from_filename(f)
        for r in rows:
            if not isinstance(r, dict):
                continue
            seed = r.get("seed")
            if seed is None:
                seed = file_seed
            records.append({
                "equation_id": r.get("equation_id"),
                "seed": seed,
                "results": r.get("results", {}),
                "_source": str(f),
            })
    return records


def compute_mean_r2_by_seed(records: list[dict], methods: list[str],
                            clip_lo: float = -10.0) -> dict:
    """Group records by seed, then compute per-seed / per-method mean test R².

    Returns a dict:
      {
        "by_seed": {seed_key: {method: {"n": int, "mean_raw": float,
                                         "mean_clip": float}}},
        "pooled":  {method: {"seed_mean_raw": [...], "mean_of_seed_means_raw": ...,
                              "sd_of_seed_means_raw": ..., "mean_of_seed_means_clip": ...,
                              "n_seeds": int}},
      }

    "pooled" mirrors _generate_pooled_seed_report() in the benchmark scripts:
    each seed is first reduced to one per-case-averaged number per method, and
    THEN those per-seed numbers are averaged — so a seed with more/duplicate
    case rows never gets extra weight relative to a seed with fewer rows.
    """
    by_seed_raw: dict = {}
    for r in records:
        seed_key = "unspecified" if r["seed"] is None else r["seed"]
        by_seed_raw.setdefault(seed_key, []).append(r)

    by_seed_out = {}
    pooled = {m: {"seed_mean_raw": [], "seeds": []} for m in methods}

    for seed_key in sorted(by_seed_raw, key=lambda k: (isinstance(k, str), k)):
        recs = by_seed_raw[seed_key]
        by_seed_out[seed_key] = {}
        for method in methods:
            vals = []
            for r in recs:
                v = r["results"].get(method, {}).get("test_r2")
                if v is not None and isinstance(v, (int, float)) and np.isfinite(v):
                    vals.append(float(v))
            if vals:
                arr = np.array(vals, dtype=float)
                mean_raw = float(np.mean(arr))
                mean_clip = float(np.mean(np.clip(arr, clip_lo, 1.0)))
                by_seed_out[seed_key][method] = {
                    "n": len(vals), "mean_raw": mean_raw, "mean_clip": mean_clip,
                }
                pooled[method]["seed_mean_raw"].append(mean_raw)
                pooled[method]["seeds"].append(seed_key)
            else:
                by_seed_out[seed_key][method] = {"n": 0, "mean_raw": None, "mean_clip": None}

    pooled_out = {}
    for method, agg in pooled.items():
        means = agg["seed_mean_raw"]
        clip_means = [float(np.mean(np.clip([m], clip_lo, 1.0))) for m in means]  # per-seed clip of its own raw mean
        pooled_out[method] = {
            "seed_mean_raw": means,
            "seeds": agg["seeds"],
            "mean_of_seed_means_raw": float(np.mean(means)) if means else float("nan"),
            "sd_of_seed_means_raw": float(np.std(means, ddof=1)) if len(means) > 1 else 0.0,
            "mean_of_seed_means_clip": float(np.mean(clip_means)) if clip_means else float("nan"),
            "n_seeds": len(means),
        }

    return {"by_seed": by_seed_out, "pooled": pooled_out}


def _print_report(report: dict, methods: list[str]):
    print("=" * 80)
    print("MEAN R² BY SEED")
    print("=" * 80)
    for seed_key, per_method in report["by_seed"].items():
        print(f"\nSeed = {seed_key}")
        for method in methods:
            m = per_method.get(method, {})
            if m.get("n"):
                print(f"  {method:15s}: mean test_r2={m['mean_raw']:.4f} "
                      f"(clip-10={m['mean_clip']:.4f}, n={m['n']})")
            else:
                print(f"  {method:15s}: no valid test_r2 values")

    print("\n" + "-" * 80)
    print("POOLED ACROSS SEEDS (each seed weighted equally)")
    print("-" * 80)
    for method in methods:
        p = report["pooled"].get(method, {})
        if p.get("n_seeds"):
            print(f"  {method:15s}: raw mean={p['mean_of_seed_means_raw']:.4f} "
                  f"± {p['sd_of_seed_means_raw']:.4f} | "
                  f"clip-10 mean={p['mean_of_seed_means_clip']:.4f} | "
                  f"n_seeds={p['n_seeds']}")
        else:
            print(f"  {method:15s}: no data")
    print("=" * 80)


def main():
    ap = argparse.ArgumentParser(
        description="Compute mean test R² by seed from HypatiaX DeFi benchmark result files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("paths", nargs="+",
                    help="Result JSON file(s) and/or directories to scan.")
    ap.add_argument("--glob", default="*results*.json",
                    help="Glob pattern used when a directory is given (default: *results*.json). "
                         "Use e.g. 'hypatiax_defi_benchmark_pca_results*.json' to restrict to one variant.")
    ap.add_argument("--methods", nargs="+", default=None,
                    help=f"Methods to report (default: {_DEFAULT_METHODS}).")
    ap.add_argument("--clip", type=float, default=-10.0,
                    help="Lower clip bound for the clip-10-style mean (default: -10.0).")
    ap.add_argument("--out", metavar="FILE", default=None,
                    help="Also write the full report as JSON to this path.")
    args = ap.parse_args()

    files = _collect_files(args.paths, args.glob)
    if not files:
        print("❌ No matching result files found.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(files)} file(s):")
    for f in files:
        print(f"  {f}")

    _warn_cross_experiment_basenames(files)

    records = _load_records(files)
    if not records:
        print("❌ No case records found in the given file(s).", file=sys.stderr)
        sys.exit(1)

    methods = args.methods or sorted({
        m for r in records for m in r["results"].keys()
    } & set(_DEFAULT_METHODS)) or _DEFAULT_METHODS

    report = compute_mean_r2_by_seed(records, methods, clip_lo=args.clip)
    _print_report(report, methods)

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
        print(f"\n📊 Report written → {args.out}")


if __name__ == "__main__":
    main()
