#!/usr/bin/env python3
"""Validate and summarize isolated all-74 exp1b_pca five-seed benchmark outputs."""
from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

SEEDS = (42, 99, 123, 777, 2024)
EXPECTED_CASES = 74
THRESHOLD = 0.999999


def result_file(directory: Path, seed: int) -> Path:
    return directory / f"hypatiax_defi_benchmark_pca_results_seed{seed}.json"


def load_and_validate(path: Path, seed: int) -> list[dict]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"FAIL: missing/empty PCA result for seed {seed}: {path}")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"FAIL: invalid JSON for seed {seed}: {path}: {exc}") from exc
    if not isinstance(rows, list) or len(rows) != EXPECTED_CASES:
        count = len(rows) if isinstance(rows, list) else type(rows).__name__
        raise SystemExit(f"FAIL: seed {seed} expected {EXPECTED_CASES} case records; got {count}")
    if not all(isinstance(row, dict) for row in rows):
        raise SystemExit(f"FAIL: seed {seed} contains non-object case records")
    observed = {row.get("seed") for row in rows}
    if observed != {seed}:
        raise SystemExit(f"FAIL: seed {seed} output has mismatched seed provenance: {observed}")
    equation_ids = [row.get("equation_id") for row in rows]
    if any(not value for value in equation_ids) or len(set(equation_ids)) != EXPECTED_CASES:
        raise SystemExit(f"FAIL: seed {seed} does not contain 74 unique equation IDs")
    return rows


def metric_undefined_reason(case: dict, arm: str) -> str | None:
    """Return the explicit reason an arm has no finite held-out R² score."""
    result = ((case.get("results") or {}).get(arm) or {})
    value = result.get("test_r2")
    if value is None:
        return str(result.get("test_r2_status") or result.get("failure_reason")
                   or "missing_test_r2")
    try:
        score = float(value)
    except (TypeError, ValueError):
        return str(result.get("test_r2_status") or "non_numeric_test_r2")
    if not math.isfinite(score):
        return str(result.get("test_r2_status") or "nonfinite_test_r2")
    return None


def finite_r2(case: dict) -> float | None:
    result = (case.get("results") or {}).get("hybrid") or {}
    value = result.get("test_r2")
    if value is None:
        for key in ("r2", "r2_test", "best_r2", "R2"):
            if case.get(key) is not None:
                value = case[key]
                break
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score) or score > 1.01:
        return None
    return score


def validate(args: argparse.Namespace) -> None:
    rows = load_and_validate(args.source, args.seed)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.source, args.destination)
    print(f"PASS: seed {args.seed}: {len(rows)} unique equations; provenance verified")
    print(f"Promoted isolated result: {args.destination}")


def finalize(args: argparse.Namespace) -> None:
    directory: Path = args.directory
    per_seed: dict[str, dict] = {}
    source_files: list[str] = []
    total_pass = total_valid = 0
    nn_undefined_metrics: list[dict] = []
    hybrid_undefined_metrics: list[dict] = []
    feature_mismatch_records: list[dict] = []
    scanned = 0

    for seed in SEEDS:
        path = result_file(directory, seed)
        rows = load_and_validate(path, seed)
        source_files.append(path.name)
        seed_pass = seed_valid = 0
        for case in rows:
            score = finite_r2(case)
            if score is not None:
                seed_valid += 1
                if score >= THRESHOLD:
                    seed_pass += 1
            equation_id = str(case.get("equation_id"))
            nn_reason = metric_undefined_reason(case, "neural_network")
            if nn_reason:
                nn_undefined_metrics.append({
                    "equation_id": equation_id, "seed": seed, "reason": nn_reason,
                })
                nn = ((case.get("results") or {}).get("neural_network") or {})
                detail = str(nn.get("error") or nn.get("failure_reason") or "")
                if "feature" in detail.lower() or "standardscaler" in detail.lower():
                    feature_mismatch_records.append({
                        "equation_id": equation_id, "seed": seed, "detail": detail,
                    })
            hybrid_reason = metric_undefined_reason(case, "hybrid")
            if hybrid_reason:
                hybrid_undefined_metrics.append({
                    "equation_id": equation_id, "seed": seed, "reason": hybrid_reason,
                })
            scanned += 1
        per_seed[str(seed)] = {
            "n_pass": seed_pass,
            "n_total": seed_valid,
            "solve_rate": seed_pass / seed_valid if seed_valid else None,
        }
        total_pass += seed_pass
        total_valid += seed_valid

    summary = {
        "fixc3_step": "exp1b_pca",
        "description": "DeFi all-74 equation seed sweep — PCA-directed 40/60 split",
        "split_protocol": "pca_40_60",
        "test_size": 0.6,
        "train_size": 0.4,
        "task_filter": "all_74_equations",
        "n_pass": total_pass,
        "n_total": total_valid,
        "solve_rate": total_pass / total_valid if total_valid else None,
        "seeds_observed": list(SEEDS),
        "n_seeds_observed": len(SEEDS),
        "expected_cases_per_seed": EXPECTED_CASES,
        "expected_case_records": EXPECTED_CASES * len(SEEDS),
        "validated_case_records": EXPECTED_CASES * len(SEEDS),
        "per_seed": per_seed,
        "source_files": source_files,
        "nn_undefined_metrics": nn_undefined_metrics,
        "hybrid_undefined_metrics": hybrid_undefined_metrics,
        "nn_feature_mismatch_records": feature_mismatch_records,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (directory / "exp1b_pca_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    disclosure = {
        "fixc3": True,
        "split_protocol": "pca_40_60",
        "split_function": "pca_directed_split",
        "split_level": "outer_loop",
        "force_fresh": True,
        "script": "hypatiax_defi_benchmark_pca.py",
        "test_size": 0.6,
        "train_size": 0.4,
        "random_split_used": False,
        "dfi_parity": True,
        "section_reference": "sec:6.4 + sec:10.2-10.4",
        "generated_by": "run_all.sh exp1b_pca isolated five-seed runner",
        "seeds": list(SEEDS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (directory / "split_protocol_disclosure.json").write_text(
        json.dumps(disclosure, indent=2), encoding="utf-8"
    )
    print(f"PASS: validated {scanned} records across seeds {list(SEEDS)}")
    print(f"PCA solve rate: {total_pass}/{total_valid}" if total_valid else
          "PCA solve rate: no finite hybrid test-R2 records")
    print(f"Summary: {directory / 'exp1b_pca_summary.json'}")
    print(f"NN undefined test-R2 metrics: {len(nn_undefined_metrics)}")
    print(f"Hybrid undefined test-R2 metrics: {len(hybrid_undefined_metrics)}")
    print(f"Confirmed NN feature-mismatch records: {len(feature_mismatch_records)}")
    for item in nn_undefined_metrics[:20]:
        print("  NN undefined:", item)


def main() -> None:
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
