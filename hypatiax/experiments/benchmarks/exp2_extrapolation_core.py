"""Canonical, side-effect-free Exp2 far-extrapolation evaluation primitives.

This module is deliberately lightweight: importing it does not seed global RNGs,
load optional ML/LLM backends, or launch experiment work.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# 0.  EXTRAPOLATION REGIME — five-tier quality ladder
#     Matches extrapolation_test_protocol.py and the comments in run_test()
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ExtrapolationRegime:
    """A single tier in the extrapolation-quality ladder."""
    name:      str    # e.g. "EXCELLENT"
    threshold: float  # upper bound of this tier (exclusive), % units
    label:     str    # human-readable label for display


#: Ordered from best to worst.  Each tier covers error_pct < threshold.
#: The last entry (CATASTROPHIC) has threshold=inf so it catches everything ≥ 500 %.
REGIMES: List[ExtrapolationRegime] = [
    ExtrapolationRegime("EXCELLENT",    50.0,       "< 50 %  EXCELLENT"),
    ExtrapolationRegime("GOOD",        100.0,       "< 100 % GOOD"),
    ExtrapolationRegime("MODERATE",    200.0,       "< 200 % MODERATE"),
    ExtrapolationRegime("POOR",        500.0,       "< 500 % POOR"),
    ExtrapolationRegime("CATASTROPHIC", float("inf"), "≥ 500 % CATASTROPHIC"),
]


def calculate_extrapolation_error(
    rmse_far: float,
    rmse_train: float,
) -> Optional[float]:
    """
    Compute extrapolation error percentage:  (RMSE_far / RMSE_train) × 100.

    Returns None when either argument is non-finite or rmse_train ≤ 0.
    A value of 100 % means the far-region RMSE exactly equals the training RMSE
    (GOOD tier boundary).
    """
    if (
        rmse_train is None
        or rmse_far is None
        or not math.isfinite(rmse_train)
        or not math.isfinite(rmse_far)
        or rmse_train <= 0.0
    ):
        return None
    return float(rmse_far / rmse_train * 100.0)


def extrapolation_error_status(error_pct: Optional[float]) -> str:
    """
    Map an extrapolation error percentage to its five-tier status label.

    Returns the regime *name* string (e.g. "EXCELLENT") so callers can
    do equality comparisons.  Returns "UNKNOWN" when error_pct is None or
    non-finite.
    """
    if error_pct is None or not math.isfinite(error_pct):
        return "UNKNOWN"
    for regime in REGIMES:
        if error_pct < regime.threshold:
            return regime.name
    return "CATASTROPHIC"  # shouldn't be reached; last tier has threshold=inf


# ──────────────────────────────────────────────────────────────────────────────
# 1.  BUILD EXTRAP SPLIT
#     Source: main() pre-processing loop, lines ~3997-4071
# ──────────────────────────────────────────────────────────────────────────────

def build_extrap_split(
    X: np.ndarray,
    y: np.ndarray,
    description: str = "",
    train_frac: float = 0.8,
    multiplier: float = 2.0,
    feature_index: Optional[int] = 0,
) -> Tuple[
    np.ndarray,   # X_train
    np.ndarray,   # y_train
    np.ndarray,   # X_far  (at least two rows)
    np.ndarray,   # y_far  (aligned with X_far)
    Dict,         # extrap metadata dict (stored in record)
]:
    """
    Re-partition (X, y) for OOD extrapolation evaluation.

    Independent directions sort on X[:, feature_index] while retaining all
    original columns. Set feature_index=None for a joint high-input direction:
    rows are ranked by mean per-feature empirical percentile. The far region
    is clipped at the selected score's training maximum plus multiplier times
    its training range. The joint score is a protocol coordinate, not a feature.

    Returns (X_train, y_train, X_far, y_far, metadata).
    Raises ValueError when the requested split cannot provide at least two
    training rows and two far-region rows after multiplier clipping.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1)
    if X.ndim != 2 or X.shape[1] < 1 or X.shape[0] != y.shape[0]:
        raise ValueError("extrapolation split requires aligned 2-D X and 1-D y arrays")
    if X.shape[0] < 4:
        raise ValueError("extrapolation split requires at least four samples")
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
        raise ValueError("extrapolation split inputs must be finite")
    if not math.isfinite(float(train_frac)) or not 0.0 < float(train_frac) < 1.0:
        raise ValueError("train_frac must be finite and strictly between 0 and 1")
    if not math.isfinite(float(multiplier)) or float(multiplier) <= 0.0:
        raise ValueError("multiplier must be finite and greater than zero")

    if feature_index is not None and (
        isinstance(feature_index, bool)
        or not isinstance(feature_index, (int, np.integer))
        or feature_index < 0
        or feature_index >= X.shape[1]
    ):
        raise ValueError(f"feature_index must be None or an index in [0, {X.shape[1]})")

    if feature_index is None:
        ranks = np.empty_like(X, dtype=float)
        for column in range(X.shape[1]):
            order_col = np.argsort(X[:, column], kind="mergesort")
            ranks[order_col, column] = np.arange(X.shape[0], dtype=float) / max(X.shape[0] - 1, 1)
        direction_score = np.mean(ranks, axis=1)
        direction_name = "joint_mean_percentile"
    else:
        direction_score = X[:, int(feature_index)]
        direction_name = f"feature_{int(feature_index)}"

    order = np.argsort(direction_score, kind="mergesort")
    Xs = X[order]
    ys = y[order]
    score_sorted = direction_score[order]
    n = len(Xs)
    split    = int(n * train_frac)
    if split < 2 or n - split < 2:
        raise ValueError(f"split leaves too few train/far rows: train={split}, far={n - split}")
    X_train  = Xs[:split]
    y_train  = ys[:split]

    # Multiplier-bounded far region.
    # far_ceiling = x_train_max + multiplier * train_range
    x_train_min = float(score_sorted[0])
    x_train_max = float(score_sorted[split - 1])
    train_range = max(x_train_max - x_train_min, 1e-300)
    far_ceiling = x_train_max + multiplier * train_range

    far_all = Xs[split:]
    far_y_all = ys[split:]
    far_mask = score_sorted[split:] <= far_ceiling
    X_far        = far_all[far_mask]
    y_far        = far_y_all[far_mask]
    if len(X_far) < 2:
        raise ValueError(f"far region has only {len(X_far)} rows after multiplier clipping")
    n_clipped    = int((~far_mask).sum())

    if n_clipped > 0:
        print(
            f"   ℹ️  '{description[:45]}': clipped {n_clipped} far sample(s) "
            f"beyond {multiplier}× boundary (x>{far_ceiling:.3g})"
        )

    metadata = {
        "extrap":            True,
        "extrap_train_frac": train_frac,
        "extrap_multiplier": multiplier,
        "extrap_n_train":    split,
        "extrap_n_test":     len(X_far),
        "extrap_x_train_max": x_train_max,
        "extrap_far_ceiling": far_ceiling,
        "extrap_direction": direction_name,
        "extrap_feature_index": feature_index,
        "extrap_direction_score": (
            "mean_empirical_percentile" if feature_index is None else "raw_feature_value"
        ),
    }

    return X_train, y_train, X_far, y_far, metadata


# ──────────────────────────────────────────────────────────────────────────────
# 2.  _RUNNER_EVAL_FORMULA  (dependency of compute_extrap_r2_far)
#     Source: BaseMethod._runner_eval_formula(), lines ~776-887
# ──────────────────────────────────────────────────────────────────────────────

def _runner_eval_formula(
    python_code: str,
    X: np.ndarray,
    var_names: List[str],
    diagnostics: Optional[List[str]] = None,
) -> Optional[np.ndarray]:
    """Evaluate formulas using the shared restricted AST interpreter."""
    from hypatiax.safe_formula import parse_formula, evaluate_expression

    try:
        X = np.asarray(X, dtype=float)
        if (
            X.ndim != 2 or X.shape[0] == 0 or X.shape[1] == 0
            or len(var_names) != X.shape[1]
            or len(set(var_names)) != len(var_names)
            or not np.all(np.isfinite(X))
        ):
            return None

        code = str(python_code).strip()
        code = re.sub(r"^\s*\[[^\]]*\]\s*", "", code)
        code = code.replace("^", "**")

        if code.startswith("def "):
            func = parse_formula(code)
            parameter_names = list(func.__signature__.parameters)
            if all(name in var_names for name in parameter_names):
                argument_columns = [var_names.index(name) for name in parameter_names]
            elif len(parameter_names) == X.shape[1]:
                # Preserve positional compatibility for older formulas whose
                # parameter names do not match the dataset's feature labels.
                argument_columns = list(range(X.shape[1]))
            else:
                missing = [name for name in parameter_names if name not in var_names]
                raise ValueError(
                    "formula parameters do not match holdout features: "
                    f"missing={missing}, features={list(var_names)}"
                )
            result = func(*(X[:, i] for i in argument_columns))
        else:
            match = re.fullmatch(
                r"\s*(?:y|result|output|pred|f)\s*=\s*(.+)",
                code, flags=re.DOTALL,
            )
            expression = match.group(1) if match else code

            namespace = {name: X[:, i] for i, name in enumerate(var_names)}
            namespace.update({
                "pi": np.pi, "e": np.e,
                "exp": lambda x: np.exp(np.clip(x, -500.0, 500.0)),
                "log": np.log, "log10": np.log10, "log2": np.log2,
                "sqrt": np.sqrt, "sin": np.sin, "cos": np.cos,
                "tan": np.tan,
                "arcsin": lambda x: np.arcsin(np.clip(x, -1.0, 1.0)),
                "arccos": lambda x: np.arccos(np.clip(x, -1.0, 1.0)),
                "arctan": np.arctan, "arctan2": np.arctan2,
                "abs": np.abs, "fabs": np.abs, "floor": np.floor,
                "ceil": np.ceil, "sign": np.sign, "power": np.power,
                "minimum": np.minimum, "maximum": np.maximum,
                "clip": np.clip, "square": np.square,
                "tanh": np.tanh, "sinh": np.sinh, "cosh": np.cosh,
                "erf": np.vectorize(math.erf),
                "erfc": np.vectorize(math.erfc),
            })
            expression = re.sub(r"\b(?:np|numpy|math)\.", "", expression)
            result = evaluate_expression(expression, namespace)

        result = np.asarray(result, dtype=float)
        if result.ndim == 0:
            result = np.full(X.shape[0], float(result))
        if result.ndim != 1 or result.shape != (X.shape[0],):
            return None
        if not np.all(np.isfinite(result)):
            return None
        return result
    except Exception as exc:
        if diagnostics is not None:
            diagnostics.append(f"{type(exc).__name__}: {exc}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# 3.  COMPUTE extrap_r2_far
#     Source: run_test() inner block, lines ~2868-2981
# ──────────────────────────────────────────────────────────────────────────────

def _far_r2(y_true: np.ndarray, y_pred: np.ndarray) -> Optional[float]:
    """
    R² on the far region with the same sign-flip correction used throughout
    the benchmark (BaseMethod._safe_r2).

    Returns None when the prediction is degenerate (non-finite, near-constant,
    or fewer than 2 samples).
    Returns float("-inf") when R² < -100 (pathological divergence).
    """
    # R2-CANONICAL: single scoring policy, see hypatiax/core/r2_canonical.py.
    # Legacy sign-flip credit is opt-in: HYPATIAX_R2_SIGN_FLIP=1.
    # NOTE: any docstring above describes the pre-canonical contract.
    try:
        from hypatiax.core.r2_canonical import r2_scored as _r2_scored
    except ImportError:  # run as a bare script, package not on sys.path
        import pathlib as _pl, sys as _sys
        for _up in _pl.Path(__file__).resolve().parents:
            if (_up / "hypatiax" / "core" / "r2_canonical.py").is_file():
                _sys.path.insert(0, str(_up))
                break
        from hypatiax.core.r2_canonical import r2_scored as _r2_scored
    _val, _status = _r2_scored(y_true, y_pred)
    if _status == "catastrophic":
        return None  # audit-M3: was float('-inf')
    return _val if _status == "ok" else None


def _far_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> Optional[float]:
    if not np.all(np.isfinite(y_pred)):
        return None
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_extrap_r2_far(
    results: Dict[str, Any],                                # {method_name: MethodResult}
    X_far: Optional[np.ndarray],
    y_far: Optional[np.ndarray],
    var_names: List[str],
    y_train: Optional[np.ndarray] = None,                   # training targets for RMSE_train
    y_pred_train: Optional[Dict[str, np.ndarray]] = None,   # {method: train predictions}
    verbose: bool = True,
    diagnostics: Optional[Dict[str, Dict[str, str]]] = None,
    X_far_predictor: Optional[np.ndarray] = None,
    X_train_predictor: Optional[np.ndarray] = None,
    prediction_audit: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[
    Dict[str, Optional[float]],   # extrap_r2_far
    Dict[str, Optional[float]],   # extrap_rmse_far
    Dict[str, Optional[float]],   # extrap_error_pct  (RMSE_far / RMSE_train × 100)
]:
    """
    Re-evaluate each method's formula on the held-out far region and return
    ``(extrap_r2_far, extrap_rmse_far, extrap_error_pct)`` dicts keyed by method name.

    Called *after* all methods have run (results already populated), inside
    run_test(), before the record is assembled.

    Parameters
    ----------
    results       : ``{name: MethodResult}`` — each entry must expose ``.success``
                    and ``.formula``.
    X_far         : held-out far-region features, shape ``(n_far, n_vars)``.
    y_far         : held-out far-region targets, shape ``(n_far,)``.
    var_names     : variable names matching X columns (e.g. ``["x0", "x1"]``).
    y_train       : training targets, used together with ``y_pred_train`` to
                    compute RMSE_train per method.
    y_pred_train  : optional pre-evaluated training predictions, keyed by method.
    X_train_predictor : original-schema training features for retained fitted
                    predictors. Used only when a method has no entry in
                    y_pred_train; these must be the exact training rows used
                    for fitting, never the far or external holdout rows.
    verbose       : print per-method far-region R² / error-% summary table.

    Returns
    -------
    extrap_r2_far    : ``{method_name: float | None}``
    extrap_rmse_far  : ``{method_name: float | None}``
    extrap_error_pct : ``{method_name: float | None}``  — (RMSE_far/RMSE_train)×100

    Notes
    -----
    A retained final fitted predictor is authoritative for both far and
    training predictions; caller-supplied arrays never override it. When no
    retained predictor exists, an evaluable symbolic formula may be used for
    far predictions and formula-derived training predictions may provide the
    RMSE baseline. The selected route is recorded in diagnostics.
    """
    extrap_r2_far:    Dict[str, Optional[float]] = {}
    extrap_rmse_far:  Dict[str, Optional[float]] = {}
    extrap_error_pct: Dict[str, Optional[float]] = {}
    _diag = diagnostics if diagnostics is not None else {}
    _audit = prediction_audit if prediction_audit is not None else {}
    _X_predict = X_far if X_far_predictor is None else X_far_predictor

    # Guard: skip entirely when not in extrap mode or far region is degenerate.
    _do_extrap = (
        X_far is not None
        and y_far is not None
        and len(X_far) > 1
        and len(y_far) > 1
    )
    if not _do_extrap:
        return extrap_r2_far, extrap_rmse_far, extrap_error_pct

    for mname, res in results.items():
        def _mark(status: str, reason: str = "") -> None:
            # Preserve detailed training/prediction diagnostics collected
            # before the final far-metric status is assigned.
            method_diag = _diag.setdefault(mname, {})
            method_diag["status"] = status
            if reason:
                method_diag["reason"] = reason

        if not getattr(res, "success", False):
            extrap_r2_far[mname] = None
            extrap_rmse_far[mname] = None
            extrap_error_pct[mname] = None
            _mark("method_failed")
            continue

        # Prefer the fitted inference callable retained by the method result.
        # It receives the original feature schema, just as the independent
        # external-holdout evaluator does; no fitting occurs on X_far.
        predictor = getattr(res, "_predict_fn", None)
        if callable(predictor):
            try:
                y_far_pred = np.asarray(predictor(_X_predict), dtype=float).reshape(-1)
            except Exception as exc:
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("prediction_error", f"{type(exc).__name__}: {exc}")
                continue
            if y_far_pred.shape != (len(y_far),):
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("prediction_length_mismatch", f"expected {len(y_far)}, got {y_far_pred.size}")
                continue
            if not np.all(np.isfinite(y_far_pred)):
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("nonfinite_prediction")
                continue
        else:
            formula = (getattr(res, "formula", None) or "").strip()
            if formula in ("N/A", ""):
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("formula_missing")
                continue
            if (
                formula.startswith("ImprovedNN(")
                or formula.startswith("[NN fallback")
            ):
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("unsupported_predictor", "architecture label has no retained _predict_fn")
                continue
            _formula_diagnostics: List[str] = []
            y_far_pred = _runner_eval_formula(formula, X_far, var_names, diagnostics=_formula_diagnostics)
            if y_far_pred is None:
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("formula_evaluation_failed", "; ".join(_formula_diagnostics) or "formula evaluator returned no prediction")
                continue
            if np.asarray(y_far_pred).shape != (len(y_far),):
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("prediction_length_mismatch", f"expected {len(y_far)}, got {np.asarray(y_far_pred).size}")
                continue
            if not np.all(np.isfinite(y_far_pred)):
                extrap_r2_far[mname] = None
                extrap_rmse_far[mname] = None
                extrap_error_pct[mname] = None
                _mark("nonfinite_prediction")
                continue

        try:
            r2f = _far_r2(y_far, y_far_pred)
            rmse_far = _far_rmse(y_far, y_far_pred)
        except Exception as exc:
            extrap_r2_far[mname] = None
            extrap_rmse_far[mname] = None
            extrap_error_pct[mname] = None
            _mark("metric_error", f"{type(exc).__name__}: {exc}")
            continue

        extrap_r2_far[mname] = r2f
        extrap_rmse_far[mname] = rmse_far
        _audit[mname] = {
            "verification_status": "recomputed_from_aligned_far_predictions",
            "prediction_source": (
                "retained_final_predictor" if callable(predictor)
                else "symbolic_formula_fallback"
            ),
            "row_count": int(len(y_far)),
            "y_true": np.asarray(y_far, dtype=float).reshape(-1).tolist(),
            "y_pred": np.asarray(y_far_pred, dtype=float).reshape(-1).tolist(),
            "r2": r2f,
            "rmse": rmse_far,
        }
        error_pct: Optional[float] = None
        error_pct_status = "training_targets_unavailable"
        predictor_route = (
            "retained_final_predictor"
            if callable(predictor)
            else "symbolic_formula_fallback"
        )
        train_prediction_route = None

        if y_train is not None and rmse_far is not None:
            train_prediction = None
            # A retained callable is the authoritative representation of the
            # final fitted method. Never let a formula-only/precomputed array
            # replace its training predictions: that would divide errors from
            # two different predictors for a hybrid method.
            if callable(predictor):
                train_prediction_route = "retained_final_predictor"
                if X_train_predictor is None:
                    error_pct_status = "training_predictor_unavailable"
                else:
                    try:
                        train_prediction = np.asarray(
                            predictor(X_train_predictor), dtype=float
                        ).reshape(-1)
                        error_pct_status = "retained_predictor"
                    except Exception as exc:
                        error_pct_status = "training_prediction_error"
                        _diag.setdefault(mname, {})["error_pct_reason"] = (
                            f"{type(exc).__name__}: {exc}"
                        )
            elif y_pred_train is not None and mname in y_pred_train:
                # In the formula fallback route, runners pre-evaluate formulas
                # on the augmented training matrix. Keep that route only when
                # no final fitted predictor exists; its provenance is recorded
                # as assumed symbolic-formula fallback for auditability.
                train_prediction = np.asarray(
                    y_pred_train[mname], dtype=float
                ).reshape(-1)
                train_prediction_route = "symbolic_formula_fallback"
                error_pct_status = "provided_formula_training_predictions"
            else:
                error_pct_status = "training_predictor_unavailable"

            if train_prediction is not None:
                train_targets = np.asarray(y_train, dtype=float).reshape(-1)
                if train_prediction.shape != train_targets.shape:
                    error_pct_status = "training_prediction_length_mismatch"
                elif not np.all(np.isfinite(train_prediction)):
                    error_pct_status = "nonfinite_training_prediction"
                elif not np.all(np.isfinite(train_targets)):
                    error_pct_status = "training_targets_invalid"
                else:
                    try:
                        rmse_train = _far_rmse(train_targets, train_prediction)
                        error_pct = calculate_extrapolation_error(rmse_far, rmse_train)
                        if error_pct is None:
                            if not math.isfinite(float(rmse_train)):
                                error_pct_status = "invalid_training_rmse"
                            elif float(rmse_train) == 0.0:
                                error_pct_status = "zero_training_rmse"
                            else:
                                error_pct_status = "invalid_far_rmse"
                        else:
                            error_pct_status = "available"

                        # Compare benchmark and extrapolation-training RMSE only
                        # when they describe the same row scope. Some adapters (notably
                        # DeFi) report metrics on the full input dataset, whereas this
                        # scorer uses only the exact extrapolation training partition.
                        method_diag = _diag.setdefault(mname, {})
                        method_diag["extrap_rmse_train"] = float(rmse_train)
                        result_metadata = getattr(res, "metadata", {}) or {}
                        provenance_fields = (
                            "evaluation_source_key",
                            "evaluation_metric_source",
                            "metric_verification_status",
                            "evaluation_prediction_source",
                            "evaluation_prediction_row_count",
                            "evaluation_feature_representation",
                            "benchmark_metric_row_count",
                            "formula_replay_status",
                            "formula_replay_max_abs_error",
                            "residual_correction_attempted",
                            "residual_correction_applied",
                            "final_predictor_composition",
                            "external_predictor_route",
                        )
                        for field in provenance_fields:
                            if field in result_metadata:
                                method_diag[field] = result_metadata[field]
                        benchmark_row_scope = result_metadata.get(
                            "benchmark_metric_row_scope", "unspecified"
                        )
                        method_diag["benchmark_rmse_row_scope"] = benchmark_row_scope
                        benchmark_rmse = getattr(res, "rmse", None)
                        if (
                            benchmark_rmse is not None
                            and isinstance(benchmark_rmse, (int, float, np.number))
                            and math.isfinite(float(benchmark_rmse))
                            and float(benchmark_rmse) >= 0.0
                        ):
                            benchmark_rmse = float(benchmark_rmse)
                            method_diag["benchmark_rmse"] = benchmark_rmse
                            if benchmark_row_scope not in ("unspecified", "extrapolation_train"):
                                method_diag["train_rmse_delta"] = None
                                method_diag["train_rmse_consistent"] = None
                                method_diag["train_rmse_consistency_status"] = (
                                    "not_comparable_different_row_scope"
                                )
                            else:
                                method_diag["train_rmse_delta"] = float(rmse_train - benchmark_rmse)
                                method_diag["train_rmse_consistent"] = math.isclose(
                                    float(rmse_train), benchmark_rmse,
                                    rel_tol=1e-6, abs_tol=1e-15,
                                )
                                method_diag["train_rmse_consistency_status"] = (
                                    "matches" if method_diag["train_rmse_consistent"]
                                    else "mismatch"
                                )
                        else:
                            method_diag["benchmark_rmse"] = None
                            method_diag["train_rmse_delta"] = None
                            method_diag["train_rmse_consistent"] = None
                            method_diag["train_rmse_consistency_status"] = "benchmark_rmse_unavailable"
                    except Exception as exc:
                        error_pct_status = "training_metric_error"
                        _diag.setdefault(mname, {})["error_pct_reason"] = (
                            f"{type(exc).__name__}: {exc}"
                        )

        extrap_error_pct[mname] = error_pct
        if r2f is None:
            _mark("r2_metric_unavailable")
        elif rmse_far is None:
            _mark("rmse_metric_unavailable")
        else:
            _mark("scored")
        method_diag = _diag.setdefault(mname, {})
        method_diag["error_pct_status"] = error_pct_status
        method_diag["predictor_route"] = predictor_route
        method_diag["training_prediction_route"] = train_prediction_route
        method_diag["error_pct_route_consistent"] = (
            train_prediction_route == predictor_route
            if train_prediction_route is not None else False
        )

    for _method_name in results:
        _audit.setdefault(_method_name, {
            "verification_status": "predictions_unavailable",
            "prediction_source": None,
            "row_count": 0,
            "y_true": None,
            "y_pred": None,
            "r2": extrap_r2_far.get(_method_name),
            "rmse": extrap_rmse_far.get(_method_name),
        })

    if verbose and any(v is not None for v in extrap_r2_far.values()):
        print(
            f"\n  📐 Extrapolation R² on far region (n={len(X_far)} held-out samples):",
            flush=True,
        )
        for mn, r2f in extrap_r2_far.items():
            r2s  = f"{r2f:.4f}" if (r2f is not None and math.isfinite(r2f)) else "null"
            pctr = extrap_error_pct.get(mn)
            pcts = f"{pctr:.1f}%" if (pctr is not None and math.isfinite(pctr)) else "null"
            tier = extrapolation_error_status(pctr)
            print(
                f"     {mn:<42} extrap_r2_far={r2s}  error_pct={pcts}  [{tier}]",
                flush=True,
            )

    return extrap_r2_far, extrap_rmse_far, extrap_error_pct
