#!/usr/bin/env python3
"""Audit the committed Random/PCA DeFi 40/60 outputs without rerunning experiments."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from hypatiax.experiments.audit.saved_results import audit_saved_files


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "hypatiax" / "data" / "results" / "comparison_results" / "noise-noiseless"
SEEDS = (42, 99, 123, 777, 2024)


def input_files() -> dict[str, list[Path]]:
    random_dir = RESULTS / "noiseless" / "defi_random_4060"
    pca_dir = RESULTS / "15_pca"
    random_files = [
        random_dir / "hypatiax_defi_benchmark_v3c_4060_results.json",
        *[
            random_dir / f"hypatiax_defi_benchmark_v3c_4060_results_seed{seed}.json"
            for seed in SEEDS if seed != 42
        ],
    ]
    pca_files = [
        pca_dir / f"hypatiax_defi_benchmark_pca_results_seed{seed}.json"
        for seed in SEEDS
    ]
    return {"random_40_60": random_files, "pca_40_60": pca_files}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "research" / "reports" / "defi-4060-symbolic-audit.json",
        help="write the post-hoc audit report here",
    )
    args = parser.parse_args()

    files = input_files()
    reports = {
        "random_40_60": audit_saved_files(
            files["random_40_60"],
            experiment_id="exp1_4060_seeds",
            split_protocol="random_40_60",
        ),
        "pca_40_60": audit_saved_files(
            files["pca_40_60"],
            experiment_id="exp1b_pca",
            split_protocol="pca_40_60",
        ),
    }
    report = {
        "schema_version": 1,
        "audit_mode": "offline_posthoc_saved_results",
        "experiments_rerun": False,
        "llm_calls_made": False,
        "training_performed": False,
        "experiments": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    for name, result in reports.items():
        print(
            f"{name}: {result['case_count']} cases; "
            f"symbolic statuses={result['symbolic_status_counts']}"
        )
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
