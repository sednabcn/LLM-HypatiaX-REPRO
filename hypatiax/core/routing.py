"""Training-only diagnostics and deterministic routing for hybrid discovery.

No target values from held-out/query data enter the route.  The degradation
probe uses only a boundary split of the training rows; KDE is fitted only to
training covariates and scores query covariates without labels.
"""
from __future__ import annotations

import ast
import re
from typing import Any

import numpy as np

STRUCTURAL_RISK_FUNCTIONS = frozenset({"exp", "log", "Phi", "sin", "cos", "erf"})


def structural_risk_tokens(*sources: str | None) -> list[str]:
    """Return exact flagged function-call names found in Python/formula text."""
    found: set[str] = set()
    for source in sources:
        if not isinstance(source, str) or not source.strip():
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            try:
                tree = ast.parse(source, mode="eval")
            except SyntaxError:
                found.update(
                    name for name in STRUCTURAL_RISK_FUNCTIONS
                    if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*\(", source)
                )
                continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else None
            )
            if name in STRUCTURAL_RISK_FUNCTIONS:
                found.add(name)
    return sorted(found)


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=float).reshape(-1)
    if y_true.shape != y_pred.shape or y_true.size < 2:
        return None
    if not np.isfinite(y_true).all() or not np.isfinite(y_pred).all():
        return None
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if not np.isfinite(ss_tot) or ss_tot <= np.finfo(float).tiny:
        return None
    value = 1.0 - float(np.sum((y_true - y_pred) ** 2)) / ss_tot
    return value if np.isfinite(value) else None


def training_edge_degradation_probe(
    X_train: Any,
    y_train: Any,
    train_predictions: Any,
    edge_fraction: float = 0.2,
) -> dict[str, Any]:
    """Measure core-to-boundary R² degradation using training rows only.

    Rows are ordered along the first principal component fitted on X_train.
    The outer `edge_fraction` of rows (both tails) form the edge probe; the
    central rows form the core.  No held-out/query targets are accepted.
    """
    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float).reshape(-1)
    pred = np.asarray(train_predictions, dtype=float).reshape(-1)
    if X.ndim != 2 or X.shape[0] != y.size or y.shape != pred.shape:
        raise ValueError("X_train, y_train, and train_predictions have incompatible shapes")
    if not 0.05 <= float(edge_fraction) <= 0.4:
        raise ValueError("edge_fraction must be between 0.05 and 0.4")
    if X.shape[0] < 12 or not np.isfinite(X).all():
        return {"status": "insufficient_or_nonfinite_training_covariates",
                "r2_core": None, "r2_edge": None, "delta": None}
    if not np.isfinite(y).all() or not np.isfinite(pred).all():
        return {"status": "nonfinite_training_targets_or_predictions",
                "r2_core": None, "r2_edge": None, "delta": None}

    # Standardise and project using training statistics only.
    scale = np.std(X, axis=0)
    scale[scale <= np.finfo(float).eps] = 1.0
    Z = (X - np.mean(X, axis=0)) / scale
    _, _, vt = np.linalg.svd(Z, full_matrices=False)
    projection = Z @ vt[0]
    order = np.argsort(projection, kind="mergesort")
    n_edge = max(2, int(np.ceil(X.shape[0] * float(edge_fraction) / 2.0)))
    if X.shape[0] - 2 * n_edge < 2:
        return {"status": "insufficient_core_rows",
                "r2_core": None, "r2_edge": None, "delta": None}
    edge_idx = np.concatenate((order[:n_edge], order[-n_edge:]))
    core_idx = order[n_edge:-n_edge]
    r2_core = _r2(y[core_idx], pred[core_idx])
    r2_edge = _r2(y[edge_idx], pred[edge_idx])
    if r2_core is None or r2_edge is None:
        return {"status": "undefined_core_or_edge_r2",
                "r2_core": r2_core, "r2_edge": r2_edge, "delta": None}
    return {
        "status": "ok", "r2_core": float(r2_core), "r2_edge": float(r2_edge),
        "delta": float(r2_core - r2_edge), "edge_fraction": float(edge_fraction),
        "n_core": int(core_idx.size), "n_edge": int(edge_idx.size),
    }


def kde_ood_probability(
    X_train: Any,
    X_query: Any,
    bandwidth: float | None = None,
) -> dict[str, Any]:
    """Estimate query OOD tail probability from a 1-D training-fitted KDE.

    PCA projection, standardisation, bandwidth, KDE and the empirical
    reference distribution are all derived from X_train only.  Query labels
    are neither accepted nor used.  p_ood is the empirical lower-density tail
    probability: larger values indicate less training-like query covariates.
    """
    train = np.asarray(X_train, dtype=float)
    query = np.asarray(X_query, dtype=float)
    if train.ndim != 2 or query.ndim != 2 or train.shape[1] != query.shape[1]:
        raise ValueError("X_train and X_query must be 2-D with matching feature counts")
    if train.shape[0] < 5 or query.shape[0] < 1:
        return {"status": "insufficient_rows", "p_ood": None}
    if not np.isfinite(train).all() or not np.isfinite(query).all():
        return {"status": "nonfinite_covariates", "p_ood": None}

    mean = np.mean(train, axis=0)
    scale = np.std(train, axis=0)
    scale[scale <= np.finfo(float).eps] = 1.0
    z_train = (train - mean) / scale
    z_query = (query - mean) / scale
    _, _, vt = np.linalg.svd(z_train, full_matrices=False)
    direction = vt[0]
    t_train = z_train @ direction
    t_query = z_query @ direction

    n = t_train.size
    if bandwidth is None:
        std = float(np.std(t_train, ddof=1))
        iqr = float(np.subtract(*np.percentile(t_train, [75, 25])))
        robust = min(std, iqr / 1.349) if iqr > 0 else std
        bandwidth = 0.9 * max(robust, 1e-8) * n ** (-1.0 / 5.0)
    bandwidth = float(bandwidth)
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("bandwidth must be a finite positive number")

    # Leave-one-out training densities avoid each reference point inflating
    # its own density.  Work in log space for numerical stability.
    d_train = (t_train[:, None] - t_train[None, :]) / bandwidth
    np.fill_diagonal(d_train, np.inf)
    train_log_kernel = -0.5 * np.square(np.clip(d_train, -1e150, 1e150))
    train_max = np.max(train_log_kernel, axis=1)
    train_log_density = (
        train_max + np.log(np.exp(train_log_kernel - train_max[:, None]).sum(axis=1))
        - np.log(n - 1) - np.log(bandwidth) - 0.5 * np.log(2.0 * np.pi)
    )
    d_query = (t_query[:, None] - t_train[None, :]) / bandwidth
    query_log_kernel = -0.5 * np.square(np.clip(d_query, -1e150, 1e150))
    query_max = np.max(query_log_kernel, axis=1)
    query_log_density = (
        query_max + np.log(np.exp(query_log_kernel - query_max[:, None]).sum(axis=1))
        - np.log(n) - np.log(bandwidth) - 0.5 * np.log(2.0 * np.pi)
    )
    # Fraction of training reference densities at least as high as query
    # density: 0 means in-distribution, 1 means strongly low-density/OOD.
    p_ood = np.mean(
        train_log_density[None, :] >= query_log_density[:, None], axis=1
    )
    return {
        "status": "ok", "p_ood": float(np.mean(p_ood)),
        "p_ood_per_query": p_ood.astype(float).tolist(),
        "bandwidth": bandwidth, "projection": "training_pca_1d",
        "reference": "training_leave_one_out_kde",
    }


def manuscript_blend_weights(p_ood: float, alpha: float = 0.3) -> dict[str, float]:
    """Apply manuscript rule w_LLM=alpha+(1-alpha)*p_OOD."""
    p_ood, alpha = float(p_ood), float(alpha)
    if not np.isfinite(p_ood) or not 0.0 <= p_ood <= 1.0:
        raise ValueError("p_ood must be finite and in [0, 1]")
    if not np.isfinite(alpha) or not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be finite and in [0, 1]")
    w_llm = alpha + (1.0 - alpha) * p_ood
    return {"llm": float(w_llm), "nn": float(1.0 - w_llm)}


def select_hypatiax_route(
    fitted_train_r2: float,
    nn_train_r2: float,
    fitted_preds_train: Any,
    nn_preds_train: Any,
    structural_tokens: list[str] | tuple[str, ...] = (),
    trust_threshold: float = 0.5,
    degradation_delta: float | None = None,
    degradation_tau: float | None = None,
    p_ood: float | None = None,
    p_ood_per_query: Any = None,
    alpha: float = 0.3,
) -> dict[str, Any]:
    """Select NN fallback, pure LLM, or ensemble using training-only diagnostics.

    Pure LLM requires a passing trust gate, no structural-risk flag, a valid
    training edge probe, and delta <= the predeclared/calibrated tau.  If tau
    is not supplied, the function fails closed to ensemble rather than
    silently inventing a threshold.  The OOD blend uses the manuscript rule.
    """
    llm_preds = np.asarray(fitted_preds_train, dtype=float) if fitted_preds_train is not None else None
    nn_preds = np.asarray(nn_preds_train, dtype=float) if nn_preds_train is not None else None
    llm_ok = (
        llm_preds is not None and llm_preds.ndim == 1 and llm_preds.size > 0
        and bool(np.isfinite(llm_preds).all()) and np.isfinite(fitted_train_r2)
        and float(fitted_train_r2) >= float(trust_threshold)
    )
    nn_ok = (
        nn_preds is not None and nn_preds.ndim == 1 and nn_preds.size > 0
        and bool(np.isfinite(nn_preds).all())
    )
    if llm_ok and nn_ok and llm_preds.shape != nn_preds.shape:
        nn_ok = False

    tokens = sorted(set(structural_tokens))
    try:
        _delta = float(degradation_delta) if degradation_delta is not None else None
    except (TypeError, ValueError):
        _delta = None
    if _delta is not None and not np.isfinite(_delta):
        _delta = None
    try:
        _tau = float(degradation_tau) if degradation_tau is not None else None
    except (TypeError, ValueError):
        _tau = None
    if _tau is not None and (not np.isfinite(_tau) or _tau < 0.0):
        _tau = None
    query_weights = None
    if p_ood_per_query is not None:
        _p_query = np.asarray(p_ood_per_query, dtype=float).reshape(-1)
        if _p_query.size and np.isfinite(_p_query).all() and np.all((_p_query >= 0.0) & (_p_query <= 1.0)):
            query_weights = {
                "llm": (alpha + (1.0 - alpha) * _p_query).astype(float).tolist(),
                "nn": (1.0 - (alpha + (1.0 - alpha) * _p_query)).astype(float).tolist(),
            }
            if p_ood is None:
                p_ood = float(np.mean(_p_query))
    base = {
        "trust_gate_passed": bool(llm_ok),
        "structural_risk_flag": bool(tokens),
        "structural_risk_tokens": tokens,
        "degradation_delta": _delta,
        "degradation_tau": _tau,
        "p_ood": (float(p_ood) if p_ood is not None and np.isfinite(p_ood) else None),
        "blend_weights": None,
        "query_blend_weights": query_weights,
    }
    if not llm_ok:
        return {**base, "decision": "nn", "predictions": nn_preds if nn_ok else None,
                "route_reason": "trust_gate_failed"}

    if tokens or _delta is None or _tau is None:
        reason = "structural_risk_precedence" if tokens else "degradation_probe_or_tau_unavailable"
        if not nn_ok:
            return {**base, "decision": "nn", "predictions": None,
                    "route_reason": reason + "_nn_unavailable"}
        weights = manuscript_blend_weights(0.0, alpha)
        predictions = weights["llm"] * llm_preds + weights["nn"] * nn_preds
        return {**base, "decision": "ensemble", "predictions": predictions,
                "route_reason": reason, "blend_weights": weights}

    if float(fitted_train_r2) >= 0.95 and _delta <= _tau:
        return {**base, "decision": "fitted_llm", "predictions": llm_preds,
                "route_reason": "trusted_high_fit_low_degradation"}

    if not nn_ok:
        return {**base, "decision": "nn", "predictions": None,
                "route_reason": "ensemble_required_nn_unavailable"}
    weights = manuscript_blend_weights(0.0, alpha)
    predictions = weights["llm"] * llm_preds + weights["nn"] * nn_preds
    return {**base, "decision": "ensemble", "predictions": predictions,
            "route_reason": "degradation_exceeds_tau_or_fit_below_0.95",
            "blend_weights": weights}
