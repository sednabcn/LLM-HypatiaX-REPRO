"""Bootstrap-estimated PC1 tail validation for Portfolio VaR.

Each replicate bootstraps rows to estimate a PC1 direction, projects the full
feature matrix onto that direction, and holds out the upper 60% of PC1 scores.
The model seed is fixed while bootstrap seeds vary. Because all feature rows
are projected and ranked, this split design remains transductive.
"""
import hashlib
import json
import os
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
from sklearn.decomposition import PCA

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
from hypatiax.tools.utils.pca_split_utils import select_case_by_identity

BOOTSTRAP_SEEDS = [
    int(value)
    for value in os.environ.get("BOOTSTRAP_PCA_SEEDS", "11,23,42,77,101").split(",")
    if value.strip()
]
MODEL_SEED = int(os.environ.get("MODEL_SEED", "42"))
TEST_SIZE = float(os.environ.get("PCA_PARTITION_TEST_SIZE", "0.6"))
OUTPUT = Path(os.environ.get(
    "PCA_PARTITION_VALIDATION_OUTPUT",
    "hypatiax/data/results/portfolio_variance_audit/"
    "portfolio_variance_bootstrap_pca_validation.json",
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


def partition_fingerprint(train_idx, test_idx):
    """Hash partition membership independent of ordering within each side."""
    membership = {
        "train": np.sort(np.asarray(train_idx, dtype=np.int64)).tolist(),
        "test": np.sort(np.asarray(test_idx, dtype=np.int64)).tolist(),
    }
    payload = json.dumps(membership, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bootstrap_pc1_partition(X, seed, test_size, feature_names):
    """Estimate PC1 on a row bootstrap, then rank all rows on that axis."""
    rng = np.random.default_rng(seed)
    n_samples = len(X)
    bootstrap_idx = rng.integers(0, n_samples, size=n_samples)
    pca = PCA(n_components=1, svd_solver="full")
    pca.fit(X[bootstrap_idx])
    scores = pca.transform(X).ravel()
    component = pca.components_[0].copy()

    # Orient PC1 consistently by making its largest-absolute loading positive.
    anchor = int(np.argmax(np.abs(component)))
    if component[anchor] < 0:
        component = -component
        scores = -scores

    order = np.lexsort((np.arange(n_samples), scores))
    split_point = max(1, min(int(n_samples * (1.0 - test_size)), n_samples - 1))
    train_idx, test_idx = order[:split_point], order[split_point:]
    metadata = {
        "bootstrap_seed": int(seed),
        "bootstrap_sample_size": int(len(bootstrap_idx)),
        "bootstrap_unique_rows": int(len(np.unique(bootstrap_idx))),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "partition_fingerprint": partition_fingerprint(train_idx, test_idx),
        "pc1_explained_variance_ratio_on_bootstrap": float(pca.explained_variance_ratio_[0]),
        "pc1_loadings": {name: float(value) for name, value in zip(feature_names, component)},
        "pc1_score_min": float(np.min(scores)),
        "pc1_score_max": float(np.max(scores)),
    }
    return train_idx, test_idx, metadata


def main():
    if not BOOTSTRAP_SEEDS:
        raise ValueError("BOOTSTRAP_PCA_SEEDS must contain at least one integer.")
    if len(set(BOOTSTRAP_SEEDS)) != len(BOOTSTRAP_SEEDS):
        raise ValueError("BOOTSTRAP_PCA_SEEDS must not contain duplicates.")
    if not 0.0 < TEST_SIZE < 1.0:
        raise ValueError("PCA_PARTITION_TEST_SIZE must be between 0 and 1.")

    from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as benchmark
    predict_and_eval = benchmark._hybrid_predict_and_eval

    protocol = DeFiExperimentProtocol()
    case_rows = []
    for domain in protocol.get_all_domains():
        for row in protocol.load_test_data(domain, num_samples=200):
            if isinstance(row, tuple) and len(row) == 5:
                description, X, y, variables, metadata = row
                case_rows.append({
                    "domain": domain, "name": description, "description": description,
                    "X": np.asarray(X), "y": np.asarray(y),
                    "variables": list(variables), "metadata": dict(metadata or {}),
                })

    case_idx, case = select_case_by_identity(
        case_rows, "risk_var", "Portfolio VaR for two correlated assets"
    )
    X = np.asarray(case["X"], dtype=float)
    y = np.asarray(case["y"]).reshape(-1)
    if len(X) != len(y):
        raise ValueError("Case feature and target row counts do not match.")
    if not np.isfinite(X).all():
        raise ValueError("Case features contain NaN or infinite values.")

    records = []
    for bootstrap_seed in BOOTSTRAP_SEEDS:
        train_idx, test_idx, split_meta = bootstrap_pc1_partition(
            X, bootstrap_seed, TEST_SIZE, case["variables"]
        )
        set_all_seeds(MODEL_SEED)
        started = time.time()
        result = predict_and_eval(
            case["description"], case["domain"],
            X[train_idx], y[train_idx], X[test_idx], y[test_idx],
            case["variables"], case["metadata"],
        )
        test_r2 = float(result["test_r2"])
        records.append({
            **split_meta,
            "model_seed": MODEL_SEED,
            "llm_train_r2": (float(result["llm_train_r2"]) if np.isfinite(result["llm_train_r2"]) else None),
            "llm_formula_train_r2_available": bool(np.isfinite(result["llm_train_r2"])),
            "tail_test_r2": test_r2,
            "test_r2_source": result.get("decision"),
            "success_tail_test_r2_gt_0_99": bool(test_r2 > 0.99),
            "time_s": float(time.time() - started),
        })
        print(
            f"bootstrap_pca_seed={bootstrap_seed} model={MODEL_SEED} "
            f"partition={split_meta['partition_fingerprint'][:12]} "
            f"decision={result.get('decision')} tail_test_r2={test_r2:.5f}"
        )

    scores = [row["tail_test_r2"] for row in records]
    unique_fingerprints = {row["partition_fingerprint"] for row in records}
    output = {
        "report_type": "portfolio_variance_bootstrap_pca_partition_validation",
        "schema_version": 1,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_identity": {
            "domain": case["domain"], "name": case["name"],
            "protocol_index": int(case_idx), "variables": case["variables"],
        },
        "protocol": {
            "split_protocol": "bootstrap_estimated_pc1_tail_40_60",
            "split_method": (
                "Fit PC1 on a size-n row bootstrap with replacement; project all "
                "feature rows; sort by oriented PC1 score; lower 40% train, upper 60% test."
            ),
            "test_size": TEST_SIZE,
            "bootstrap_pca_seeds": BOOTSTRAP_SEEDS,
            "model_seed_fixed": MODEL_SEED,
            "n_samples": int(len(X)),
            "split_is_transductive": True,
            "feature_scaling": "none; raw features",
            "interpretation": (
                "Repeated bootstrap-estimated PC1 tail partitions. This is a "
                "transductive sensitivity analysis and is distinct from both "
                "the original full-data PCA split and random-holdout interpolation."
            ),
            "score_semantics": {
                "llm_train_r2": (
                    "LLM formula training R2 only; NaN means unavailable or invalid, "
                    "not NN training failure."
                ),
                "tail_test_r2": "Test R2 from the selected route in test_r2_source.",
                "test_r2_source": "Selected benchmark route, e.g. nn, llm, or ensemble.",
            },
            "partition_fingerprint_semantics": (
                "SHA-256 of sorted train and test row indices; equal fingerprints "
                "mean identical partition membership, regardless of index order."
            },
        },
        "results": records,
        "aggregate": {
            "n_bootstrap_replicates": len(records),
            "n_unique_partitions": len(unique_fingerprints),
            "n_duplicate_partition_replicates": len(records) - len(unique_fingerprints),
            "all_replicates_same_partition": len(unique_fingerprints) == 1,
            "n_success_tail_test_r2_gt_0_99": sum(
                row["success_tail_test_r2_gt_0_99"] for row in records
            ),
            "success_rate_tail_test_r2_gt_0_99": float(np.mean([
                row["success_tail_test_r2_gt_0_99"] for row in records
            ])),
            "tail_test_r2_mean": float(np.mean(scores)),
            "tail_test_r2_sample_std": float(np.std(scores, ddof=1)) if len(scores) > 1 else 0.0,
            "tail_test_r2_min": float(np.min(scores)),
            "tail_test_r2_max": float(np.max(scores)),

        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(
        f"Unique partitions: {len(unique_fingerprints)}/{len(records)} "
        f"(duplicate replicates: {len(records) - len(unique_fingerprints)})"
    )
    print(f"Saved bootstrap PCA validation: {OUTPUT}")


if __name__ == "__main__":
    main()
