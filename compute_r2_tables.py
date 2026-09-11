#!/usr/bin/env python3
"""
compute_r2_tables.py — Mean R^2 tables for exp1 / exp1_pca / 15 / 15_pca
================================================================================

Reads the result JSON files produced by run_all.sh's exp1, exp1_pca, exp1b
(-> comparison_results/noise-noiseless/15) and exp1b_pca (-> .../15_pca)
steps, groups every per-case R^2 value by seed (42, 99, 123, 777, 2024), and
builds one table per experiment with:

    seed | n_cases | mean_R2

plus an "ALL" row with the overall mean across every seed.

It relies on the same output-directory layout and R^2-extraction logic used
by run_all.sh itself (see the exp1_pca_summary.json / exp1b_pca_summary.json
generation blocks in that script). Table/output labels below use the actual
result-directory names rather than the run_all.sh step names, since that's
what's on disk (per tree_r.txt):

    exp1        -> ${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi
    exp1_pca    -> ${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi_pca
    15          -> ${RESULTS_DIR}/comparison_results/noise-noiseless/15         (exp1b step)
    15_pca      -> ${RESULTS_DIR}/comparison_results/noise-noiseless/15_pca     (exp1b_pca step)

For every case record it looks for R^2 at:
    results.hybrid.test_r2                      (primary, matches run_all.sh)
    then falls back to: r2 / r2_test / best_r2 / R2   (top-level keys)

Records without a resolvable 'seed' field are still counted in an "unknown"
bucket so nothing silently disappears, but they are excluded from the 5
requested-seed rows and from the ALL mean (mirrors how run_all.sh's own
per_seed summary only reports seeds it actually saw).

Usage
-----
    python3 compute_r2_tables.py --results-dir /path/to/hypatiax/data/results
    python3 compute_r2_tables.py --results-dir /path/to/results --out-dir ./r2_tables

If --results-dir is omitted, it defaults to "./hypatiax/data/results" (the
same default-relative layout run_all.sh assumes when run from REPO_ROOT).

Outputs
-------
- Prints a Markdown table per experiment to stdout.
- Writes one CSV per experiment plus a combined CSV to --out-dir
  (default: ./r2_tables).
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from statistics import mean

TARGET_SEEDS = [42, 99, 123, 777, 2024]

# Files to always skip regardless of which experiment directory we're scanning.
SKIP_SUBSTRINGS = ("checkpoint", "disclosure", "summary", "baseline")

# Keys here become the table headers, source labels, and *_r2_by_seed.csv
# filenames -- kept as the literal on-disk directory names ("15" / "15_pca")
# rather than the run_all.sh step names ("exp1b" / "exp1b_pca") they came from,
# per tree_r.txt.
EXPERIMENTS = {
    "exp1": "comparison_results/noise-noiseless/noiseless/defi",
    "exp1_pca": "comparison_results/noise-noiseless/noiseless/defi_pca",
    "15": "comparison_results/noise-noiseless/15",
    "15_pca": "comparison_results/noise-noiseless/15_pca",
}

# NOTE: exp1 / exp1_pca are NOT guaranteed single-seed. hypatiax_defi_benchmark_v3c.py's
# run_benchmark() loops over DEFI_SEEDS; exp1b/exp1b_pca set DEFI_SEEDS explicitly per
# shard, but the plain exp1/exp1_pca steps in run_all.sh don't set it at all, so the
# script falls back to ITS OWN default seed list -- the same 42,99,123,777,2024 used
# everywhere else in this pipeline (see the exp1b/exp1b_pca SHARD_SEEDS fallback in
# run_all.sh). So exp1/exp1_pca can legitimately produce files/records for all 5 seeds,
# not just 42 -- do not special-case or default them. A file with no seed anywhere
# (neither a per-case field nor a filename token) is counted as truly unresolved rather
# than guessed, the same as any other experiment.

# Matches "seed42", "seed_42", "seed-42" (case-insensitive) anywhere in a filename,
# e.g. hypatiax_defi_benchmark_v3_results_seed99.json,
#      hypatiax_defi_benchmark_pca_results_seed2024.json,
#      hypatiax_defi_benchmark_v3_results_shard0_seed42_99.json (shard-tagged exp1b move)
SEED_FILENAME_RE = re.compile(r"seed[_-]?(\d+)", re.IGNORECASE)


def seed_from_filename(name: str):
    """Best-effort seed extraction from a result filename. Returns int or None.
    If the filename encodes more than one seed (e.g. a shard file that was tagged
    with a comma-joined seed list like '..._seed42_99.json' from run_all.sh's
    exp1b move block), only the first one is used and it's still a single value
    per file -- multi-seed-per-file shard tags are rare and mean every case in
    that file legitimately shares one seed anyway (each shard runs one DEFI_SEEDS
    value at a time per the FIX-exp1b-SEED-SHARD comment in run_all.sh)."""
    m = SEED_FILENAME_RE.search(name)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def extract_r2(case: dict):
    """Same extraction order run_all.sh's own summary blocks use."""
    hybrid = case.get("results", {}).get("hybrid", {}) if isinstance(case.get("results"), dict) else {}
    r2 = hybrid.get("test_r2")
    if r2 is None:
        for k in ("r2", "r2_test", "best_r2", "R2"):
            v = case.get(k)
            if v is not None:
                r2 = v
                break
    if r2 is None:
        return None
    try:
        r2 = float(r2)
    except (TypeError, ValueError):
        return None
    if r2 > 1.01:  # same sanity guard run_all.sh applies
        return None
    return r2


def normalize_seed(seed):
    if seed is None:
        return None
    try:
        return int(seed)
    except (TypeError, ValueError):
        return None


def load_cases(exp_dir: Path, exp_name: str, seed_source_counts: dict):
    """Yield (equation_id, seed, r2) for every case record found under exp_dir,
    de-duplicated on (equation_id, seed, source stem-without-shard) the same
    way run_all.sh's exp1b_pca_summary.json generator dedups across shards.

    Seed resolution order (most to least authoritative), matching how
    run_all.sh actually names/tags these files:
      1. The case record's own 'seed' field (present when hypatiax_defi_
         benchmark_v3c.py / _pca.py stamp it per-record).
      2. A 'seedNN' token in the filename -- applies uniformly to all four
         experiments: exp1's hypatiax_defi_benchmark_v3_results_seed{42,99,
         123,777,2024}.json, exp1_pca's hypatiax_defi_benchmark_pca_results_
         seed{N}.json, exp1b/exp1b_pca's per-seed files, and any shard-suffixed
         move-block output like '..._shard0_seed42.json'.
      3. Otherwise: seed stays None and the case is counted in the 'unknown'
         bucket by build_table() -- nothing is silently lost, and nothing is
         guessed. (exp1_pca's single un-suffixed hypatiax_defi_benchmark_pca_
         results.json, if that's genuinely all that exists, will land here.)
    """
    if not exp_dir.exists():
        return

    seen = set()
    for fp in sorted(exp_dir.glob("*.json")):
        if any(s in fp.name for s in SKIP_SUBSTRINGS):
            continue
        try:
            data = json.loads(fp.read_text())
        except Exception as e:
            print(f"  [WARN] Could not parse {fp}: {e}", file=sys.stderr)
            continue

        cases = data if isinstance(data, list) else data.get("results", [data])
        if not isinstance(cases, list):
            continue

        file_seed = seed_from_filename(fp.name)

        for case in cases:
            if not isinstance(case, dict):
                continue
            eq_id = case.get("equation_id") or case.get("case") or case.get("name")

            field_seed = normalize_seed(case.get("seed"))
            if field_seed is not None:
                seed = field_seed
                seed_source_counts["from_field"] += 1
            elif file_seed is not None:
                seed = file_seed
                seed_source_counts["from_filename"] += 1
            else:
                seed = None
                seed_source_counts["unresolved"] += 1

            key = (eq_id, seed, fp.name)
            if key in seen:
                continue
            seen.add(key)

            r2 = extract_r2(case)
            if r2 is None:
                continue
            yield eq_id, seed, r2


def build_table(exp_dir: Path, exp_name: str):
    per_seed = {s: [] for s in TARGET_SEEDS}
    unknown_seed_r2 = []
    other_seed_r2 = {}
    seed_source_counts = {"from_field": 0, "from_filename": 0, "unresolved": 0}

    for _eq_id, seed, r2 in load_cases(exp_dir, exp_name, seed_source_counts):
        if seed is None:
            unknown_seed_r2.append(r2)
        elif seed in per_seed:
            per_seed[seed].append(r2)
        else:
            other_seed_r2.setdefault(seed, []).append(r2)

    rows = []
    all_vals = []
    for s in TARGET_SEEDS:
        vals = per_seed[s]
        all_vals.extend(vals)
        rows.append({
            "seed": s,
            "n_cases": len(vals),
            "mean_r2": mean(vals) if vals else None,
        })

    rows.append({
        "seed": "ALL (5 target seeds)",
        "n_cases": len(all_vals),
        "mean_r2": mean(all_vals) if all_vals else None,
    })

    extras = {
        "unknown_seed_n": len(unknown_seed_r2),
        "other_seeds_seen": sorted(other_seed_r2.keys()),
        "seed_source_counts": seed_source_counts,
    }
    return rows, extras


def fmt_r2(v):
    return f"{v:.6f}" if v is not None else "n/a"


def print_markdown(title: str, exp_dir: Path, rows, extras):
    print(f"\n### {title}")
    print(f"_source dir: `{exp_dir}`_\n")
    print("| Seed | N cases | Mean R² |")
    print("|---|---|---|")
    for r in rows:
        print(f"| {r['seed']} | {r['n_cases']} | {fmt_r2(r['mean_r2'])} |")
    if extras["unknown_seed_n"]:
        print(f"\n_Note: {extras['unknown_seed_n']} case(s) had no resolvable seed (no per-case 'seed' field "
              f"and no seedNN token in the filename) and were excluded above._")
    if extras["other_seeds_seen"]:
        print(f"_Note: seed(s) {extras['other_seeds_seen']} were present in the data but are outside the requested list {TARGET_SEEDS}._")
    ssc = extras["seed_source_counts"]
    print(f"\n_Seed resolution: {ssc['from_field']} from case record, {ssc['from_filename']} from filename, "
          f"{ssc['unresolved']} unresolved (no seed field or filename token)._")


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "n_cases", "mean_r2"])
        for r in rows:
            w.writerow([r["seed"], r["n_cases"], "" if r["mean_r2"] is None else r["mean_r2"]])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-dir", default="hypatiax/data/results",
                     help="RESULTS_DIR used by run_all.sh (default: hypatiax/data/results)")
    ap.add_argument("--out-dir", default="r2_tables",
                     help="Where to write per-experiment CSV tables (default: ./r2_tables)")
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    out_dir = Path(args.out_dir)

    combined_rows = []
    for exp_name, rel_path in EXPERIMENTS.items():
        exp_dir = results_dir / rel_path
        rows, extras = build_table(exp_dir, exp_name)
        print_markdown(exp_name, exp_dir, rows, extras)
        write_csv(out_dir / f"{exp_name}_r2_by_seed.csv", rows)
        for r in rows:
            combined_rows.append({"experiment": exp_name, **r})

    combined_path = out_dir / "all_experiments_r2_by_seed.csv"
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    with combined_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["experiment", "seed", "n_cases", "mean_r2"])
        for r in combined_rows:
            w.writerow([r["experiment"], r["seed"], r["n_cases"], "" if r["mean_r2"] is None else r["mean_r2"]])

    print(f"\nCSV tables written to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
