"""
hypatiax/core/metrics.py
========================
Regression and symbolic-regression evaluation metrics for HypatiaX.

Paper: "HypatiaX: A Hybrid Symbolic-Neural Framework for
        Extrapolation-Reliable Analytical Discovery"  (JMLR v3.0, Apr 2026)

Public API
----------
compute_r2(y_true, y_pred)                  → float
compute_mse(y_true, y_pred)                 → float
compute_rmse(y_true, y_pred)                → float
compute_mae(y_true, y_pred)                 → float
compute_max_error(y_true, y_pred)           → float
compute_near_perfect_rate(scores, thr)      → float   # §10.2: R²>0.99 rate
compute_catastrophic_rate(scores, thr)      → float   # §10.2: R²<-1 rate (NaN counts)
compute_exact_recovery_rate(scores, thr)    → float   # strict 0.999999 rate
compute_speedup(t_baseline, t_system)       → float
evaluate_all(y_true, y_pred)               → dict

All functions accept array-like inputs (list, np.ndarray, pd.Series).
NumPy is the only hard dependency; scikit-learn is used when available
for cross-validation of R² but is never required at import time.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Union

import numpy as np

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------
ArrayLike = Union[Sequence[float], np.ndarray]

# ---------------------------------------------------------------------------
# Threshold policy (single source of truth -- import these, don't re-hardcode)
# ---------------------------------------------------------------------------
NEAR_PERFECT_THRESHOLD = 0.99        # cross-condition comparison threshold
EXACT_RECOVERY_THRESHOLD = 0.999999  # strict "exact recovery" threshold
CATASTROPHIC_THRESHOLD = -1.0

# Constant-target detection is RELATIVE to the target's scale. A fixed
# absolute cutoff on the total sum of squares misclassifies legitimately
# small-scale targets (e.g. values ~1e-6) as constant and silently scores
# them 0.0.
_REL_EPS = 1e-12


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_array(x: ArrayLike, name: str = "array") -> np.ndarray:
    """Convert array-like to a 1-D float64 numpy array."""
    arr = np.asarray(x, dtype=np.float64).ravel()
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1-D after ravelling, got shape {arr.shape}")
    return arr


def _validate_pair(y_true: ArrayLike, y_pred: ArrayLike):
    """Return validated (y_true, y_pred) arrays of equal length."""
    yt = _to_array(y_true, "y_true")
    yp = _to_array(y_pred, "y_pred")
    if len(yt) != len(yp):
        raise ValueError(
            f"y_true and y_pred must have the same length "
            f"({len(yt)} vs {len(yp)})"
        )
    if len(yt) == 0:
        raise ValueError("Arrays must not be empty")
    return yt, yp


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def compute_r2(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """
    Coefficient of determination (R²).

    R² = 1 - SS_res / SS_tot

    Returns
    -------
    float
        R² ∈ (-∞, 1].
        * NaN when *y_pred* contains NaN or inf (a failed prediction -- callers
          must count it as a failure, not as a missing cell).
        * -inf is possible when SS_res overflows; also a failure.
        * Constant target (SS_tot ~ 0 *relative to the scale of y_true*):
          1.0 if the prediction is also exact, otherwise 0.0, matching
          sklearn's ``force_finite`` behaviour.

    Raises
    ------
    ValueError
        If *y_true* contains NaN or inf (a data bug, never silently scored).

    Examples
    --------
    >>> compute_r2([1, 2, 3], [1, 2, 3])
    1.0
    >>> round(compute_r2([1, 2, 3], [1, 2, 4]), 4)
    0.5
    >>> compute_r2([1, 2, 3], [1, float("nan"), 3])
    nan
    >>> round(compute_r2([1e-6, 2e-6, 3e-6], [1e-6, 2e-6, 4e-6]), 4)
    0.5
    """
    yt, yp = _validate_pair(y_true, y_pred)
    if not np.all(np.isfinite(yt)):
        raise ValueError("y_true contains NaN or inf")
    if not np.all(np.isfinite(yp)):
        return float("nan")
    with np.errstate(over="ignore", invalid="ignore"):
        ss_res = float(np.sum((yt - yp) ** 2))
        ss_tot = float(np.sum((yt - np.mean(yt)) ** 2))
        scale = float(np.sum(yt ** 2))
    if ss_tot <= _REL_EPS * scale:
        # constant target
        return 1.0 if ss_res <= _REL_EPS * scale else 0.0
    return float(1.0 - ss_res / ss_tot)


def compute_mse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """
    Mean Squared Error.

    MSE = (1/n) Σ (y_true - y_pred)²

    Examples
    --------
    >>> compute_mse([0, 1], [1, 1])
    0.5
    """
    yt, yp = _validate_pair(y_true, y_pred)
    return float(np.mean((yt - yp) ** 2))


def compute_rmse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """
    Root Mean Squared Error.

    RMSE = sqrt(MSE)

    Examples
    --------
    >>> round(compute_rmse([0, 1], [1, 1]), 6)
    0.707107
    """
    return math.sqrt(compute_mse(y_true, y_pred))


def compute_mae(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """
    Mean Absolute Error.

    MAE = (1/n) Σ |y_true - y_pred|

    Examples
    --------
    >>> compute_mae([0, 1, 2], [0, 0, 2])
    0.3333333333333333
    """
    yt, yp = _validate_pair(y_true, y_pred)
    return float(np.mean(np.abs(yt - yp)))


def compute_max_error(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """
    Maximum absolute error (L∞ norm of residuals).

    Examples
    --------
    >>> compute_max_error([0, 1, 2], [0, 0, 2])
    1.0
    """
    yt, yp = _validate_pair(y_true, y_pred)
    return float(np.max(np.abs(yt - yp)))


# ---------------------------------------------------------------------------
# HypatiaX paper-specific aggregate metrics (§10.2, §10.4)
# ---------------------------------------------------------------------------

def compute_near_perfect_rate(
    scores: ArrayLike,
    threshold: float = NEAR_PERFECT_THRESHOLD,
) -> float:
    """
    Fraction of tasks whose R² exceeds *threshold*.

    NaN scores (failed predictions) stay in the denominator and never count
    as passes.

    Paper target (§10.2): 89.2 % of DeFi 74-task benchmark at R²>0.99.

    Examples
    --------
    >>> compute_near_perfect_rate([0.995, 0.98, 0.999], threshold=0.99)
    0.6666666666666666
    >>> compute_near_perfect_rate([0.995, float("nan")], threshold=0.99)
    0.5
    """
    arr = _to_array(scores, "scores")
    if len(arr) == 0:
        return float("nan")
    return float(np.mean(arr > threshold))


def compute_exact_recovery_rate(
    scores: ArrayLike,
    threshold: float = EXACT_RECOVERY_THRESHOLD,
) -> float:
    """
    Fraction of tasks at the strict exact-recovery threshold (default
    0.999999).  Report this *alongside* the 0.99 rate: at 0.99 nearly every
    method saturates, so it cannot separate systems on its own.

    Examples
    --------
    >>> compute_exact_recovery_rate([1.0, 0.9995, 0.5])
    0.3333333333333333
    """
    return compute_near_perfect_rate(scores, threshold)


def compute_catastrophic_rate(
    scores: ArrayLike,
    threshold: float = CATASTROPHIC_THRESHOLD,
    nan_as_failure: bool = True,
) -> float:
    """
    Fraction of tasks whose R² is below *threshold* (catastrophic failures).

    NaN scores (failed / non-finite predictions) count as catastrophic by
    default (``nan_as_failure=True``); ``-inf`` is below any threshold.

    Paper target (§10.2): 0 catastrophic failures (R²<-1).

    Examples
    --------
    >>> compute_catastrophic_rate([0.9, -2.0, 0.5])
    0.3333333333333333
    >>> compute_catastrophic_rate([0.9, float("nan"), float("-inf"), 0.5])
    0.5
    >>> compute_catastrophic_rate([0.9, float("nan")], nan_as_failure=False)
    0.0
    """
    arr = _to_array(scores, "scores")
    if len(arr) == 0:
        return float("nan")
    fails = arr < threshold
    if nan_as_failure:
        fails = fails | np.isnan(arr)
    return float(np.mean(fails))


def compute_speedup(t_baseline: float, t_system: float) -> float:
    """
    Speedup ratio: baseline wall-time / system wall-time.

    Paper target (§10.4): 1.73× speedup for LLM-routed cases.

    Parameters
    ----------
    t_baseline : float
        Wall-clock time of the baseline method (seconds).
    t_system : float
        Wall-clock time of HypatiaX (seconds).

    Returns
    -------
    float
        Speedup ≥ 0.  Returns inf when t_system == 0.

    Examples
    --------
    >>> round(compute_speedup(1.73, 1.0), 2)
    1.73
    """
    if t_system < 0 or t_baseline < 0:
        raise ValueError("Times must be non-negative")
    if t_system == 0.0:
        return float("inf")
    return float(t_baseline / t_system)


# ---------------------------------------------------------------------------
# Convenience bundle
# ---------------------------------------------------------------------------

def evaluate_all(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    *,
    near_perfect_threshold: float = NEAR_PERFECT_THRESHOLD,
    exact_recovery_threshold: float = EXACT_RECOVERY_THRESHOLD,
    catastrophic_threshold: float = CATASTROPHIC_THRESHOLD,
) -> dict:
    """
    Compute all scalar metrics for a single prediction array and return
    them as a plain dict.

    Returned keys
    -------------
    r2, mse, rmse, mae, max_error,
    valid         (bool -- all predictions finite),
    near_perfect  (bool -- R² > near_perfect_threshold),
    exact         (bool -- R² > exact_recovery_threshold),
    catastrophic  (bool -- R² < catastrophic_threshold, or R² is NaN)

    A non-finite prediction gives ``valid=False``, ``near_perfect=False``,
    ``exact=False``, ``catastrophic=True`` -- never a silent pass.

    Examples
    --------
    >>> m = evaluate_all([1, 2, 3], [1, 2, 3])
    >>> m['r2'], m['catastrophic'], m['valid']
    (1.0, False, True)
    >>> m = evaluate_all([1, 2, 3], [1, float("nan"), 3])
    >>> m['valid'], m['near_perfect'], m['catastrophic']
    (False, False, True)
    """
    r2 = compute_r2(y_true, y_pred)
    r2_nan = math.isnan(r2)
    return {
        "r2":           r2,
        "mse":          compute_mse(y_true, y_pred),
        "rmse":         compute_rmse(y_true, y_pred),
        "mae":          compute_mae(y_true, y_pred),
        "max_error":    compute_max_error(y_true, y_pred),
        "valid":        bool(np.all(np.isfinite(_to_array(y_pred, "y_pred")))),
        "near_perfect": bool((not r2_nan) and r2 > near_perfect_threshold),
        "exact":        bool((not r2_nan) and r2 > exact_recovery_threshold),
        "catastrophic": bool(r2_nan or r2 < catastrophic_threshold),
    }


# ---------------------------------------------------------------------------
# Backwards-compat shims
# ---------------------------------------------------------------------------
# statistical_analysis.py originally did:
#   from hypatiax.core import metrics
#   metrics.compute_r2(...)
# All names are already at module level so that usage works unchanged.

r2_score  = compute_r2    # sklearn-style alias
mean_squared_error   = compute_mse
root_mean_squared_error = compute_rmse
mean_absolute_error  = compute_mae


# ---------------------------------------------------------------------------
# Self-test (python -m hypatiax.core.metrics)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import doctest
    results = doctest.testmod(verbose=False)
    if results.failed:
        raise SystemExit(f"{results.failed} doctest(s) failed")

    # Spot-check against sklearn when available
    try:
        import sklearn.metrics as _skm  # cross-check only; not an evaluator
        _skl_r2 = _skm.r2_score
        _yt = np.random.default_rng(42).normal(size=200)
        _yp = _yt + np.random.default_rng(0).normal(scale=0.1, size=200)
        _ours  = compute_r2(_yt, _yp)
        _theirs = float(_skl_r2(_yt, _yp))
        assert abs(_ours - _theirs) < 1e-10, f"R² mismatch: {_ours} vs {_theirs}"
        print(f"✓ R² matches sklearn ({_ours:.6f})")
    except ImportError:
        print("sklearn not installed — skipping cross-check")

    # Regression tests for the evaluator guard / NaN handling
    assert abs(compute_r2([1e-6, 2e-6, 3e-6], [1e-6, 2e-6, 4e-6]) - 0.5) < 1e-9, \
        "small-scale target must not be treated as constant"
    assert math.isnan(compute_r2([1, 2, 3], [1, float("inf"), 3]))
    assert compute_r2([5, 5, 5], [5, 5, 5]) == 1.0
    assert compute_r2([5, 5, 5], [5, 5, 6]) == 0.0
    assert evaluate_all([1, 2, 3], [float("nan")] * 3)["catastrophic"] is True
    try:
        compute_r2([1, float("nan")], [1, 2])
    except ValueError:
        pass
    else:
        raise AssertionError("NaN y_true must raise")

    print("✓ All metrics self-tests passed")
