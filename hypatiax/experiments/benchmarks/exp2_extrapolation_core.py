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
) -> Tuple[
    np.ndarray,   # X_train
    np.ndarray,   # y_train
    np.ndarray,   # X_far  (at least two rows)
    np.ndarray,   # y_far  (aligned with X_far)
    Dict,         # extrap metadata dict (stored in record)
]:
    """
    Re-partition (X, y) for OOD extrapolation evaluation.

    Training covers the first `train_frac` of the sample range (sorted by
    X[:,0]).  The far region is the remainder, clipped at
    x_train_max + multiplier * train_range so the evaluation regime matches
    repro.yaml benchmarks.feynman.extrap_mult=2.0.

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

    # Sort by first variable to get a contiguous training region.
    order    = np.argsort(X[:, 0])
    Xs       = X[order]
    ys       = y[order]
    n        = len(Xs)
    split    = int(n * train_frac)
    if split < 2 or n - split < 2:
        raise ValueError(f"split leaves too few train/far rows: train={split}, far={n - split}")
    X_train  = Xs[:split]
    y_train  = ys[:split]

    # Multiplier-bounded far region.
    # far_ceiling = x_train_max + multiplier * train_range
    x_train_min  = float(Xs[0, 0])
    x_train_max  = float(Xs[split - 1, 0])
    train_range  = max(x_train_max - x_train_min, 1e-300)
    far_ceiling  = x_train_max + multiplier * train_range

    far_all      = Xs[split:]
    far_y_all    = ys[split:]
    far_mask     = far_all[:, 0] <= far_ceiling
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
    y_pred_train  : ``{method_name: np.ndarray}`` of per-method training
                    predictions pre-evaluated by the caller (only symbolic
                    methods included).  When provided, RMSE_train is derived
                    from these; otherwise ``extrap_error_pct`` is null for all
                    methods.
    verbose       : print per-method far-region R² / error-% summary table.

    Returns
    -------
    extrap_r2_far    : ``{method_name: float | None}``
    extrap_rmse_far  : ``{method_name: float | None}``
    extrap_error_pct : ``{method_name: float | None}``  — (RMSE_far/RMSE_train)×100

    Notes
    -----
    Methods that return NN architecture tags (``"ImprovedNN(…)"``,
    ``"[NN fallback"``, ``"N/A"``, ``""``) are skipped — they have no evaluable
    expression so all three values are null.  Only SymbolicEngineWithLLM and
    HybridDiscoverySystem v50_2 produce formula strings and yield non-null values.
    """
    extrap_r2_far:    Dict[str, Optional[float]] = {}
    extrap_rmse_far:  Dict[str, Optional[float]] = {}
    extrap_error_pct: Dict[str, Optional[float]] = {}
    _diag = diagnostics if diagnostics is not None else {}
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
            _diag[mname] = {"status": status, **({"reason": reason} if reason else {})}

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
        error_pct: Optional[float] = None
        if (
            rmse_far is not None and y_pred_train is not None
            and y_train is not None and mname in y_pred_train
        ):
            try:
                rmse_train = _far_rmse(y_train, y_pred_train[mname])
                error_pct = calculate_extrapolation_error(rmse_far, rmse_train)
            except Exception as exc:
                _mark("metric_error", f"training RMSE: {type(exc).__name__}: {exc}")
        extrap_error_pct[mname] = error_pct
        if r2f is None:
            _mark("r2_metric_unavailable")
        elif rmse_far is None:
            _mark("rmse_metric_unavailable")
        else:
            _mark("scored")

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
