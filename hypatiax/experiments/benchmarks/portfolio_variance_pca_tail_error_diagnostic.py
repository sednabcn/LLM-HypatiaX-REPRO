"""Diagnose NN prediction errors on the existing Portfolio VaR PCA tail split."""
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
from hypatiax.tools.utils.pca_split_utils import select_case_by_identity

TEST_SIZE = float(os.environ.get("PCA_ERROR_TEST_SIZE", "0.6"))
OUTPUT = Path(os.environ.get(
    "PCA_ERROR_DIAGNOSTIC_OUTPUT",
    "hypatiax/data/results/portfolio_variance_audit/"
    "portfolio_variance_pca_tail_error_diagnostic.json",
))


def regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=float).reshape(-1)
    if len(y_true) != len(y_pred) or not len(y_true):
        raise ValueError("Metric inputs must have equal, non-zero lengths.")
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mean_signed_error_prediction_minus_actual": float(np.mean(y_pred - y_true)),
        "median_absolute_error": float(np.median(np.abs(y_pred - y_true))),
    }


def build_pca_split(X, test_size):
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or len(X) < 2 or not np.isfinite(X).all():
        raise ValueError("X must be a finite 2D matrix with at least two rows.")
    if not 0.0 < test_size < 1.0:
        raise ValueError("PCA_ERROR_TEST_SIZE must be between 0 and 1.")
    pca = PCA(n_components=1, svd_solver="full")
    scores = pca.fit_transform(X).ravel()
    loadings = pca.components_[0].copy()
    anchor = int(np.argmax(np.abs(loadings)))
    if loadings[anchor] < 0:
        loadings = -loadings
        scores = -scores
    order = np.lexsort((np.arange(len(X)), scores))
    n_train = max(1, min(int(len(X) * (1.0 - test_size)), len(X) - 1))
    return order[:n_train], order[n_train:], scores, loadings, pca


def expand_test_predictions(n_samples, test_indices, test_predictions):
    expanded = np.full(n_samples, np.nan, dtype=float)
    expanded[np.asarray(test_indices, dtype=int)] = np.asarray(test_predictions, dtype=float)
    return expanded


def decile_diagnostics(y_true, y_pred_all, pc1_scores, test_indices, n_deciles=10):
    ordered_test = np.asarray(test_indices)[
        np.argsort(np.asarray(pc1_scores)[test_indices], kind="mergesort")
    ]
    chunks = np.array_split(ordered_test, min(n_deciles, len(ordered_test)))
    rows = []
    for decile, indices in enumerate(chunks, start=1):
        actual = np.asarray(y_true)[indices]
        predicted = np.asarray(y_pred_all)[indices]
        errors = predicted - actual
        rows.append({
            "pc1_test_decile": decile,
            "n": int(len(indices)),
            "pc1_score_min": float(np.min(pc1_scores[indices])),
            "pc1_score_max": float(np.max(pc1_scores[indices])),
            "target_mean": float(np.mean(actual)),
            "prediction_mean": float(np.mean(predicted)),
            "mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
            "mean_signed_error_prediction_minus_actual": float(np.mean(errors)),
            "r2": float(r2_score(actual, predicted)) if len(indices) >= 2 else None,
            "row_indices": [int(i) for i in indices],
        })
    return rows


def main():
    if TEST_SIZE != 0.6:
        print(f"WARNING: using non-default test fraction {TEST_SIZE}; standard PCA protocol uses 0.6.")

    protocol = DeFiExperimentProtocol()
    case_rows = []
    for domain in protocol.get_all_domains():
        for item in protocol.load_test_data(domain, num_samples=200):
            if isinstance(item, tuple) and len(item) == 5:
                description, X, y, variables, metadata = item
                case_rows.append({
                    "domain": domain, "name": description, "description": description,
                    "X": np.asarray(X, dtype=float), "y": np.asarray(y, dtype=float).reshape(-1),
                    "variables": list(variables), "metadata": dict(metadata or {}),
                })
    _, case = select_case_by_identity(
        case_rows, "risk_var", "Portfolio VaR for two correlated assets"
    )
    X, y = case["X"], case["y"]
    if len(X) != len(y) or not np.isfinite(y).all():
        raise ValueError("Feature and target dimensions must match and targets must be finite.")

    train_idx, test_idx, pc1_scores, loadings, pca = build_pca_split(X, TEST_SIZE)

    # Reuse the exact NN implementation and seed configured by this benchmark.
    from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as benchmark
    nn_seed = int(benchmark._NN_SEED)
    started = time.time()
    nn_result = benchmark._train_and_eval_nn(
        X[train_idx], y[train_idx], X[test_idx], y[test_idx], seed=nn_seed
    )
    elapsed = time.time() - started
    if not nn_result.get("success", False):
        raise RuntimeError("Benchmark NN helper did not report success.")
    y_pred_test = np.asarray(nn_result["y_pred_test"], dtype=float).reshape(-1)
    y_pred_train = np.asarray(nn_result["y_pred_train"], dtype=float).reshape(-1)
    if len(y_pred_test) != len(test_idx) or not np.isfinite(y_pred_test).all():
        raise ValueError("NN test predictions are missing, misaligned, or non-finite.")

    baseline_value = float(np.mean(y[train_idx]))
    baseline_pred = np.full(len(test_idx), baseline_value, dtype=float)
    model_metrics = regression_metrics(y[test_idx], y_pred_test)
    baseline_metrics = regression_metrics(y[test_idx], baseline_pred)
    pred_all = expand_test_predictions(len(y), test_idx, y_pred_test)

    row_predictions = []
    for local_pos, row_idx in enumerate(test_idx):
        actual = float(y[row_idx])
        predicted = float(y_pred_test[local_pos])
        row_predictions.append({
            "row_index": int(row_idx),
            "pc1_score": float(pc1_scores[row_idx]),
            "actual_target": actual,
            "predicted_target": predicted,
            "prediction_minus_actual": predicted - actual,
            "absolute_error": abs(predicted - actual),
            "baseline_prediction": baseline_value,
            "baseline_absolute_error": abs(baseline_value - actual),
            "features": {
                name: float(X[row_idx, j])
                for j, name in enumerate(case["variables"])
            },
        })
    row_predictions.sort(key=lambda item: item["pc1_score"])

    output = {
        "report_type": "portfolio_variance_pca_tail_error_diagnostic",
        "schema_version": 1,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_identity": {
            "domain": case["domain"], "name": case["name"],
            "variables": case["variables"],
        },
        "protocol": {
            "split_protocol": "pca_40_60_pc1",
            "split_method": "PCA(n_components=1) on all raw, unstandardized feature rows; lower 40% train, upper 60% test",
            "split_is_transductive": True,
            "n_samples": int(len(X)), "n_train": int(len(train_idx)), "n_test": int(len(test_idx)),
            "test_size": TEST_SIZE,
            "model": "benchmark _train_and_eval_nn helper, including train-derived augmentation and scaling",
            "nn_seed": nn_seed,
            "llm_called": False,
            "benchmark_modified": False,
            "interpretation": "NN-only diagnostic on the existing PCA partition; it isolates NN tail prediction errors and does not reproduce LLM/hybrid routing.",
        },
        "pca": {
            "explained_variance_ratio_pc1": float(pca.explained_variance_ratio_[0]),
            "loadings_oriented_largest_absolute_positive": {
                name: float(value) for name, value in zip(case["variables"], loadings)
            },
            "last_train_pc1_score": float(pc1_scores[train_idx[-1]]),
            "first_test_pc1_score": float(pc1_scores[test_idx[0]]),
            "score_gap_across_cutoff": float(pc1_scores[test_idx[0]] - pc1_scores[train_idx[-1]]),
        },
        "model": {
            "decision_scope": "NN only; prior benchmark runs reported decision='nn' for this case",
            "train_r2": float(nn_result["train_r2"]),
            "test_metrics": model_metrics,
            "timed_out": bool(nn_result.get("timed_out", False)),
            "runtime_seconds": float(elapsed),
        },
        "training_mean_baseline": {
            "prediction_value": baseline_value,
            "test_metrics": baseline_metrics,
            "model_minus_baseline_r2": float(model_metrics["r2"] - baseline_metrics["r2"]),
            "model_mae_divided_by_baseline_mae": (
                float(model_metrics["mae"] / baseline_metrics["mae"])
                if baseline_metrics["mae"] > 0 else None
            ),
        },
        "test_error_by_pc1_decile": decile_diagnostics(
            y, pred_all, pc1_scores, test_idx
        ),
        "test_predictions_sorted_by_pc1": row_predictions,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(f"NN seed: {nn_seed}; timed_out={nn_result.get('timed_out', False)}")
    print(f"Model test R2={model_metrics['r2']:.6f}, MAE={model_metrics['mae']:.6f}, RMSE={model_metrics['rmse']:.6f}")
    print(f"Mean baseline R2={baseline_metrics['r2']:.6f}, MAE={baseline_metrics['mae']:.6f}, RMSE={baseline_metrics['rmse']:.6f}")
    print(f"Model-minus-baseline R2={model_metrics['r2'] - baseline_metrics['r2']:.6f}")
    print(f"Saved PCA tail error diagnostic: {OUTPUT}")


if __name__ == "__main__":
    main()
