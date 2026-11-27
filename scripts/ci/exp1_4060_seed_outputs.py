#!/usr/bin/env python3
"""Validate and summarize the exp1_4060 random 40/60 sweep.

The R² threshold is a predictive-score diagnostic, not a symbolic-solve metric.
"""
from __future__ import annotations
import argparse, json, math, shutil
from datetime import datetime, timezone
from pathlib import Path

SEEDS = (42, 99, 123, 777, 2024)
EXPECTED_CASES = 74
THRESHOLD = 0.999999
PREFIX = "hypatiax_defi_benchmark_v3c_4060_results"

def result_file(directory: Path, seed: int) -> Path:
    suffix = "" if seed == 42 else f"_seed{seed}"
    return directory / f"{PREFIX}{suffix}.json"

def load_rows(path: Path, seed: int) -> list[dict]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"FAIL: missing/empty result for seed {seed}: {path}")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"FAIL: invalid JSON for seed {seed}: {exc}") from exc
    if not isinstance(rows, list) or len(rows) != EXPECTED_CASES:
        raise SystemExit(f"FAIL: seed {seed} expected {EXPECTED_CASES} records; got {len(rows) if isinstance(rows, list) else type(rows).__name__}")
    if not all(isinstance(row, dict) for row in rows):
        raise SystemExit(f"FAIL: seed {seed} contains non-object records")
    observed_seeds = {row.get("seed") for row in rows}
    if observed_seeds != {seed}:
        raise SystemExit(f"FAIL: seed {seed} has mismatched provenance: {observed_seeds}")
    ids = [row.get("equation_id") for row in rows]
    if any(not value for value in ids) or len(set(ids)) != EXPECTED_CASES:
        raise SystemExit(f"FAIL: seed {seed} does not contain 74 unique equation IDs")
    for row in rows:
        protocol = row.get("split_protocol") or {}
        if protocol.get("name") != "random_40_60":
            raise SystemExit(f"FAIL: seed {seed} has unexpected split metadata: {protocol.get('name')}")
        if protocol.get("test_fraction") != 0.6:
            raise SystemExit(f"FAIL: seed {seed} has unexpected test_fraction: {protocol.get('test_fraction')}")
    return rows

def finite_r2(row: dict) -> float | None:
    result = (row.get("results") or {}).get("hybrid") or {}
    value = result.get("test_r2")
    if value is None:
        for key in ("r2", "r2_test", "best_r2", "R2"):
            if row.get(key) is not None:
                value = row[key]
                break
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if math.isfinite(score) and score <= 1.01 else None

def is_near_perfect_predictive_pass(row: dict, threshold: float = THRESHOLD) -> bool:
    """Classify a finite held-out R² threshold pass; never call it symbolic recovery."""
    score = finite_r2(row)
    return score is not None and score >= threshold


def validate(args):
    rows = load_rows(args.source, args.seed)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.source, args.destination)
    print(f"PASS: seed {args.seed}: {len(rows)} unique equations, seed and random_40_60 metadata verified")

def finalize(args):
    directory = args.directory
    per_seed, sources = {}, []
    total_pass = total_valid = 0
    for seed in SEEDS:
        path = result_file(directory, seed)
        rows = load_rows(path, seed)
        sources.append(path.name)
        n_predictive_pass = n_valid = 0
        for row in rows:
            score = finite_r2(row)
            if score is not None:
                n_valid += 1
                n_predictive_pass += int(is_near_perfect_predictive_pass(row))
        per_seed[str(seed)] = {
            "n_near_perfect_predictive_r2": n_predictive_pass,
            "n_finite_test_r2": n_valid,
            "near_perfect_predictive_r2_rate": (
                n_predictive_pass / n_valid if n_valid else None
            ),
        }
        total_pass += n_predictive_pass
        total_valid += n_valid
    summary = {
        "experiment_id": "exp1_4060_seeds",
        "description": "DeFi all-74 benchmark — seeded random 40/60 split",
        "split_protocol": "random_40_60",
        "split_function": "_random_split_random_40_60",
        "train_size": 0.4, "test_size": 0.6,
        "seeds_observed": list(SEEDS), "n_seeds_observed": len(SEEDS),
        "expected_cases_per_seed": EXPECTED_CASES,
        "validated_case_records": EXPECTED_CASES * len(SEEDS),
        "metric_definition": "fraction of finite hybrid held-out R2 scores >= 0.999999; not symbolic equivalence",
        "threshold": THRESHOLD,
        "n_near_perfect_predictive_r2": total_pass,
        "n_finite_test_r2": total_valid,
        "near_perfect_predictive_r2_rate": (
            total_pass / total_valid if total_valid else None
        ),
        "per_seed": per_seed, "source_files": sources,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (directory / "exp1_4060_seeds_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    disclosure = {
        "experiment_id": "exp1_4060_seeds",
        "split_protocol": "random_40_60",
        "split_function": "_random_split_random_40_60",
        "split_level": "outer_loop",
        "train_size": 0.4, "test_size": 0.6,
        "random_split_used": True, "random_state_policy": "one seeded permutation per benchmark seed; reused across cases with matching row counts",
        "force_fresh": True, "script": "hypatiax_defi_benchmark_v3c_4060.py",
        "seeds": list(SEEDS),
        "generated_by": "run_all.sh exp1_4060_seeds isolated five-seed runner",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (directory / "split_protocol_disclosure.json").write_text(json.dumps(disclosure, indent=2), encoding="utf-8")
    print(f"PASS: validated {EXPECTED_CASES * len(SEEDS)} raw case records across {len(SEEDS)} seeds")
    print(f"Random 40/60 near-perfect predictive R2 pass rate (NOT symbolic recovery): {total_pass}/{total_valid} ({summary['near_perfect_predictive_r2_rate']:.6f})" if total_valid else "No valid hybrid R2 records")

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate")
    check.add_argument("--source", type=Path, required=True)
    check.add_argument("--destination", type=Path, required=True)
    check.add_argument("--seed", type=int, choices=SEEDS, required=True)
    check.set_defaults(func=validate)
    summary = sub.add_parser("finalize")
    summary.add_argument("--directory", type=Path, required=True)
    summary.set_defaults(func=finalize)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
