"""Compare raw-feature rankings with the PC1-directed Portfolio VaR split."""
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
from scipy.stats import rankdata
from sklearn.decomposition import PCA

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
from hypatiax.tools.utils.pca_split_utils import select_case_by_identity

TRAIN_FRACTION = float(os.environ.get("FEATURE_RANKING_TRAIN_FRACTION", "0.4"))
BOUNDARY_ROWS = int(os.environ.get("FEATURE_RANKING_BOUNDARY_ROWS", "5"))
OUTPUT = Path(os.environ.get(
    "FEATURE_RANKING_DIAGNOSTIC_OUTPUT",
    "hypatiax/data/results/portfolio_variance_audit/"
    "portfolio_variance_feature_ranking_diagnostic.json",
))


def spearman(x, y):
    rx = rankdata(np.asarray(x, dtype=float), method="average")
    ry = rankdata(np.asarray(y, dtype=float), method="average")
    if np.std(rx) == 0 or np.std(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def membership_metrics(reference, candidate, n):
    a, b = set(map(int, reference)), set(map(int, candidate))
    union, intersection = a | b, a & b
    return {
        "train_membership_jaccard_vs_pc1": float(len(intersection) / len(union)) if union else 1.0,
        "train_membership_agreement_fraction_vs_pc1": float(
            (len(intersection) + (n - len(union))) / n
        ),
        "n_train_rows_in_common": len(intersection),
        "n_train_rows_different": len(a ^ b),
    }


def analyze(X, y, names):
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float).reshape(-1)
    names = [str(v) for v in names]
    if X.ndim != 2 or X.shape[1] != len(names) or len(X) != len(y) or len(X) < 2:
        raise ValueError("Invalid feature/target dimensions or feature names.")
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("Features and target must be finite.")
    if not 0 < TRAIN_FRACTION < 1 or BOUNDARY_ROWS < 1:
        raise ValueError("Invalid train fraction or boundary row count.")

    n = len(X)
    cut = max(1, min(int(n * TRAIN_FRACTION), n - 1))
    row = np.arange(n)
    pca = PCA(n_components=1, svd_solver="full")
    scores = pca.fit_transform(X).ravel()
    loadings = pca.components_[0].copy()
    anchor = int(np.argmax(np.abs(loadings)))
    if loadings[anchor] < 0:
        loadings, scores = -loadings, -scores

    pc_order = np.lexsort((row, scores))
    pc_train = pc_order[:cut]
    feature_comparisons = []
    for j, name in enumerate(names):
        values = X[:, j]
        order = np.lexsort((row, values))
        corr = spearman(values, scores)
        feature_comparisons.append({
            "feature": name,
            "spearman_correlation_with_pc1_score": corr,
            "absolute_spearman_correlation_with_pc1_score": abs(corr) if corr is not None else None,
            "feature_train_split_vs_pc1": membership_metrics(pc_train, order[:cut], n),
            "feature_summary": {
                "min": float(values.min()), "max": float(values.max()),
                "mean": float(values.mean()), "std": float(values.std()),
                "unique_values": int(len(np.unique(values))),
            },
        })

    first = feature_comparisons[0]
    start, stop = max(0, cut - BOUNDARY_ROWS), min(n, cut + BOUNDARY_ROWS)
    boundary = []
    for pos in range(start, stop):
        idx = int(pc_order[pos])
        boundary.append({
            "pc1_order_position_zero_based": pos,
            "side": "train_edge" if pos < cut else "test_edge",
            "row_index": idx,
            "pc1_score": float(scores[idx]),
            "target": float(y[idx]),
            "features": {name: float(X[idx, j]) for j, name in enumerate(names)},
        })

    return {
        "protocol": {
            "split_protocol": "full_data_raw_feature_pc1_vs_individual_feature_rankings",
            "train_fraction": TRAIN_FRACTION, "test_fraction": 1.0 - TRAIN_FRACTION,
            "n_samples": n, "n_features": X.shape[1], "n_train": cut, "n_test": n - cut,
            "pca_fit": "PCA(n_components=1) on all raw, unstandardized feature rows",
            "split_is_transductive": True,
            "interpretation": "Descriptive diagnostic only; no model training or benchmark split changes.",
        },
        "pca": {
            "explained_variance_ratio_pc1": float(pca.explained_variance_ratio_[0]),
            "loadings_oriented_largest_absolute_positive": {
                name: float(v) for name, v in zip(names, loadings)
            },
            "pc1_score_min": float(scores.min()), "pc1_score_max": float(scores.max()),
        },
        "feature_comparisons": feature_comparisons,
        "first_feature_comparison": {
            "feature": names[0],
            "spearman_correlation_with_pc1_score": first["spearman_correlation_with_pc1_score"],
            **first["feature_train_split_vs_pc1"],
            "exact_same_train_membership_as_pc1": (
                first["feature_train_split_vs_pc1"]["train_membership_jaccard_vs_pc1"] == 1.0
            ),
        },
        "pc1_cutoff": {
            "split_position_zero_based": cut,
            "last_train_pc1_score": float(scores[pc_order[cut - 1]]),
            "first_test_pc1_score": float(scores[pc_order[cut]]),
            "score_gap_across_cutoff": float(scores[pc_order[cut]] - scores[pc_order[cut - 1]]),
            "boundary_rows_each_side_requested": BOUNDARY_ROWS,
            "rows": boundary,
        },
    }


def main():
    protocol = DeFiExperimentProtocol()
    cases = []
    for domain in protocol.get_all_domains():
        for item in protocol.load_test_data(domain, num_samples=200):
            if isinstance(item, tuple) and len(item) == 5:
                description, X, y, variables, metadata = item
                cases.append({
                    "domain": domain, "name": description, "description": description,
                    "X": np.asarray(X), "y": np.asarray(y),
                    "variables": list(variables), "metadata": dict(metadata or {}),
                })
    _, case = select_case_by_identity(
        cases, "risk_var", "Portfolio VaR for two correlated assets"
    )
    result = {
        "report_type": "portfolio_variance_feature_ranking_diagnostic",
        "schema_version": 1,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_identity": {
            "domain": case["domain"], "name": case["name"], "variables": case["variables"]
        },
        **analyze(case["X"], case["y"], case["variables"]),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"PC1 explained variance ratio: {result['pca']['explained_variance_ratio_pc1']:.8f}")
    for item in result["feature_comparisons"]:
        corr = item["spearman_correlation_with_pc1_score"]
        corr_text = "undefined" if corr is None else f"{corr:.6f}"
        m = item["feature_train_split_vs_pc1"]
        print(
            f"feature={item['feature']} spearman={corr_text} "
            f"train_jaccard={m['train_membership_jaccard_vs_pc1']:.6f} "
            f"train_agreement={m['train_membership_agreement_fraction_vs_pc1']:.6f}"
        )
    c = result["pc1_cutoff"]
    print(
        f"PC1 cutoff gap={c['score_gap_across_cutoff']:.8g}; "
        f"last_train={c['last_train_pc1_score']:.8g}; "
        f"first_test={c['first_test_pc1_score']:.8g}"
    )
    print(f"Saved feature-ranking diagnostic: {OUTPUT}")


if __name__ == "__main__":
    main()
