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

from hypatiax.core.r2_canonical import r2_checked

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
    """Use the repository's canonical R² policy for routing diagnostics."""
    value, status = r2_checked(y_true, y_pred)
    return float(value) if status == "ok" and np.isfinite(value) else None


def training_edge_split_indices(
    X_train: Any, edge_fraction: float = 0.15
) -> tuple[np.ndarray, np.ndarray]:
    """Return (core_indices, edge_indices) from both tails of a training-only PCA axis."""
    X = np.asarray(X_train, dtype=float)
    if X.ndim != 2 or X.shape[0] < 12 or X.shape[1] < 1:
        raise ValueError("X_train must be a 2-D array with at least 12 rows and one feature")
    if not np.isfinite(X).all():
        raise ValueError("X_train must contain only finite covariates")
    if not 0.05 <= float(edge_fraction) <= 0.4:
        raise ValueError("edge_fraction must be between 0.05 and 0.4")
    scale = np.std(X, axis=0)
    if not np.any(scale > np.finfo(float).eps):
        raise ValueError("X_train has no varying covariates for a PCA edge split")
    scale[scale <= np.finfo(float).eps] = 1.0
    Z = (X - np.mean(X, axis=0)) / scale
    _, _, vt = np.linalg.svd(Z, full_matrices=False)
    order = np.argsort(Z @ vt[0], kind="mergesort")
    n_edge_side = max(2, int(np.ceil(X.shape[0] * float(edge_fraction) / 2.0)))
    if X.shape[0] - 2 * n_edge_side < 2:
        raise ValueError("edge_fraction leaves too few core rows")
    edge = np.concatenate((order[:n_edge_side], order[-n_edge_side:]))
    core = order[n_edge_side:-n_edge_side]
    return core.astype(int), edge.astype(int)


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
    if train.ndim != 2 or query.ndim != 2 or train.shape[1] < 1 or train.shape[1] != query.shape[1]:
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
    if float(np.std(t_train)) <= np.finfo(float).eps:
        return {"status": "degenerate_training_projection", "p_ood": None,
                "p_ood_per_query": []}

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


def route_decision_from_diagnostics(
    trust_gate_passed: bool,
    fitted_train_r2: float,
    structural_tokens: list[str] | tuple[str, ...] = (),
    degradation_delta: float | None = None,
    degradation_tau: float | None = None,
) -> dict[str, Any]:
    """Central five-stage route decision from training-only diagnostics."""
    tokens = sorted(set(structural_tokens))
    if not trust_gate_passed:
        return {"decision": "nn", "route_reason": "trust_gate_failed",
                "structural_risk_flag": bool(tokens), "structural_risk_tokens": tokens}
    if tokens:
        return {"decision": "ensemble", "route_reason": "structural_risk_precedence",
                "structural_risk_flag": True, "structural_risk_tokens": tokens}
    try:
        delta = float(degradation_delta) if degradation_delta is not None else None
    except (TypeError, ValueError):
        delta = None
    if delta is not None and not np.isfinite(delta):
        delta = None
    try:
        tau = float(degradation_tau) if degradation_tau is not None else None
    except (TypeError, ValueError):
        tau = None
    if tau is not None and (not np.isfinite(tau) or tau < 0.0):
        tau = None
    if delta is None or tau is None:
        return {"decision": "ensemble",
                "route_reason": "degradation_probe_or_tau_unavailable",
                "structural_risk_flag": False, "structural_risk_tokens": []}
    try:
        train_r2 = float(fitted_train_r2)
    except (TypeError, ValueError):
        train_r2 = float("nan")
    if np.isfinite(train_r2) and train_r2 >= 0.95 and delta <= tau:
        return {"decision": "fitted_llm",
                "route_reason": "trusted_high_fit_low_degradation",
                "structural_risk_flag": False, "structural_risk_tokens": []}
    return {"decision": "ensemble",
            "route_reason": "degradation_exceeds_tau_or_fit_below_0.95",
            "structural_risk_flag": False, "structural_risk_tokens": []}


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
    try:
        train_r2 = float(fitted_train_r2)
        trust_cutoff = float(trust_threshold)
        trust_values_valid = (
            not isinstance(fitted_train_r2, (bool, np.bool_))
            and not isinstance(trust_threshold, (bool, np.bool_))
            and np.isfinite(train_r2) and np.isfinite(trust_cutoff)
        )
    except (TypeError, ValueError, OverflowError):
        train_r2, trust_cutoff, trust_values_valid = float("nan"), float("nan"), False
    llm_ok = (
        llm_preds is not None and llm_preds.ndim == 1 and llm_preds.size > 0
        and bool(np.isfinite(llm_preds).all()) and trust_values_valid
        and train_r2 >= trust_cutoff
    )
    try:
        # Validate alpha before constructing either scalar or per-query weights.
        alpha = float(alpha)
        if not np.isfinite(alpha) or not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be finite and in [0, 1]")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("alpha must be finite and in [0, 1]") from exc
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
        try:
            _p_query = np.asarray(p_ood_per_query, dtype=float).reshape(-1)
        except (TypeError, ValueError, OverflowError):
            _p_query = np.asarray([], dtype=float)
        if _p_query.size and np.isfinite(_p_query).all() and np.all((_p_query >= 0.0) & (_p_query <= 1.0)):
            _query_llm = alpha + (1.0 - alpha) * _p_query
            query_weights = {
                "llm": _query_llm.astype(float).tolist(),
                "nn": (1.0 - _query_llm).astype(float).tolist(),
            }
            if p_ood is None:
                p_ood = float(np.mean(_p_query))
    try:
        _p_ood = float(p_ood) if p_ood is not None else None
    except (TypeError, ValueError, OverflowError):
        _p_ood = None
    if _p_ood is not None and (
        not np.isfinite(_p_ood) or not 0.0 <= _p_ood <= 1.0
    ):
        _p_ood = None
    base = {
        "trust_gate_passed": bool(llm_ok),
        "structural_risk_flag": bool(tokens),
        "structural_risk_tokens": tokens,
        "degradation_delta": _delta,
        "degradation_tau": _tau,
        "p_ood": _p_ood,
        "blend_weights": None,
        "query_blend_weights": query_weights,
    }
    if not llm_ok:
        return {**base, "decision": "nn", "predictions": nn_preds if nn_ok else None,
                "route_reason": "trust_gate_failed"}

    policy = route_decision_from_diagnostics(
        True, fitted_train_r2, tokens, _delta, _tau
    )
    if policy["decision"] == "fitted_llm":
        return {**base, "decision": "fitted_llm", "predictions": llm_preds,
                "route_reason": policy["route_reason"]}

    if not nn_ok:
        return {**base, "decision": "nn", "predictions": None,
                "route_reason": policy["route_reason"] + "_nn_unavailable"}
    weights = manuscript_blend_weights(0.0, alpha)
    predictions = weights["llm"] * llm_preds + weights["nn"] * nn_preds
    return {**base, "decision": "ensemble", "predictions": predictions,
            "route_reason": policy["route_reason"], "blend_weights": weights}
