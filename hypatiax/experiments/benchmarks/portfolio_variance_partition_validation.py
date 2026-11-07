"""Repeated random-holdout control for the Portfolio VaR case.

This is deliberately separate from the transductive PC1-tail extrapolation
benchmark. It tests sensitivity to independently sampled 40/60 partitions;
it does not measure far-range extrapolation.
"""
import json
import os
import random
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
from hypatiax.tools.utils.pca_split_utils import select_case_by_identity

PARTITION_SEEDS = [
    int(value)
    for value in os.environ.get("PARTITION_SEEDS", "11,23,42,77,101").split(",")
    if value.strip()
]
MODEL_SEED = int(os.environ.get("MODEL_SEED", "42"))
TEST_SIZE = float(os.environ.get("PARTITION_TEST_SIZE", "0.6"))
OUTPUT = Path(os.environ.get(
    "PARTITION_VALIDATION_OUTPUT",
    "hypatiax/data/results/portfolio_variance_audit/"
    "portfolio_variance_random_holdout_validation.json",
))


def set_all_seeds(seed):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
    except ImportError:
        pass


def main():
    if not PARTITION_SEEDS:
        raise ValueError("PARTITION_SEEDS must contain at least one integer.")
    if not 0.0 < TEST_SIZE < 1.0:
        raise ValueError("PARTITION_TEST_SIZE must be between 0 and 1.")

    # Match the benchmark's prediction/evaluation implementation.
    from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as benchmark
    predict_and_eval = benchmark._hybrid_predict_and_eval

    protocol = DeFiExperimentProtocol()
    records = []
    domains = list(protocol.get_all_domains())
    case_rows = []
    for domain in domains:
        for row in protocol.load_test_data(domain, num_samples=200):
            if isinstance(row, tuple) and len(row) == 5:
                description, X, y, variables, metadata = row
                case_rows.append({
                    "domain": domain,
                    "name": description,
                    "description": description,
                    "X": np.asarray(X),
                    "y": np.asarray(y),
                    "variables": list(variables),
                    "metadata": dict(metadata or {}),
                })

    case_idx, case = select_case_by_identity(
        case_rows, "risk_var", "Portfolio VaR for two correlated assets"
    )
    X = np.asarray(case["X"])
    y = np.asarray(case["y"]).reshape(-1)
    if len(X) != len(y):
        raise ValueError("Case feature and target row counts do not match.")

    for partition_seed in PARTITION_SEEDS:
        train_idx, test_idx = train_test_split(
            np.arange(len(X)),
            test_size=TEST_SIZE,
            random_state=partition_seed,
            shuffle=True,
        )
        set_all_seeds(MODEL_SEED)
        started = time.time()
        result = predict_and_eval(
            case["description"],
            case["domain"],
            X[train_idx],
            y[train_idx],
            X[test_idx],
            y[test_idx],
            case["variables"],
            case["metadata"],
        )
        records.append({
            "partition_seed": partition_seed,
            "model_seed": MODEL_SEED,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "train_r2": float(result["train_r2"]),
            "test_r2": float(result["test_r2"]),
            "success": bool(result["test_r2"] > 0.99),
            "decision": result.get("decision"),
            "time_s": float(time.time() - started),
        })
        print(
            f"partition={partition_seed} model={MODEL_SEED} "
            f"train_r2={result['train_r2']:.5f} "
            f"test_r2={result['test_r2']:.5f}"
        )

    test_scores = [row["test_r2"] for row in records]
    output = {
        "report_type": "portfolio_variance_random_holdout_partition_validation",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_identity": {
            "domain": case["domain"],
            "name": case["name"],
            "protocol_index": int(case_idx),
            "variables": case["variables"],
        },
        "protocol": {
            "split_protocol": "independent_random_holdout_40_60",
            "split_method": "sklearn train_test_split on row indices",
            "test_size": TEST_SIZE,
            "partition_seeds": PARTITION_SEEDS,
            "model_seed_fixed": MODEL_SEED,
            "n_samples": int(len(X)),
            "split_is_transductive": False,
            "interpretation": (
                "Random-holdout interpolation/control; not the PC1-directed "
                "far-range extrapolation protocol."
            ),
        },
        "results": records,
        "aggregate": {
            "n_partitions": len(records),
            "n_success": sum(row["success"] for row in records),
            "success_rate": sum(row["success"] for row in records) / len(records),
            "test_r2_mean": float(np.mean(test_scores)),
            "test_r2_sample_std": float(np.std(test_scores, ddof=1)) if len(test_scores) > 1 else 0.0,
            "test_r2_min": float(np.min(test_scores)),
            "test_r2_max": float(np.max(test_scores)),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Saved partition validation: {OUTPUT}")


if __name__ == "__main__":
    main()
