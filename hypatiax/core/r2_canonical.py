"""Single source of truth for R^2 scoring in HypatiaX.

Ported from LLM-HypatiaX-Hybrid ``rsc/methods/metrics.py`` so both repos can
share one policy. Pure numpy; safe to import from subprocess workers.

Policy
------
* Degenerate target (variance relative to sum of squares <= REL_TOL):
  R^2 is undefined -> (nan, "degenerate_target"). Never 0.0, never 1.0.
* Non-finite prediction -> (-inf, "nonfinite_pred"). A failure.
* Wrong-shaped prediction -> (-inf, "bad_shape"). A failure.
* Otherwise R^2 = 1 - ss_res / ss_tot, status "ok".

``r2_checked`` / ``r2`` implement exactly that. ``r2_scored`` (used by the
benchmark scorers) adds the guards those scorers always had: out-of-range
predictions and R^2 < -100 are reported as -inf so they cannot swamp a mean.

The tolerance is RELATIVE, so physically tiny but varying targets (Newton
gravity ~1e-11, Photon ~1e-19, Zeeman ~1e-23) are scored normally.

Legacy sign-flip credit
-----------------------
Older benchmark scorers ("FIX 1") re-scored a prediction with its sign
negated when that gave a better R^2, so that a correct magnitude with the
opposite sign convention was not punished. That is NOT part of the canonical
policy: a wrong-sign formula is a wrong formula. It is kept as an explicit
opt-in so previously published numbers can be reproduced:

    HYPATIAX_R2_SIGN_FLIP=1  python run_...        # legacy scoring

or per call: ``r2_scored(y, p, sign_flip=True)``.

Aggregate with status counts, not bare means: nan and -inf must never be
averaged silently.
"""
from __future__ import annotations

import os

import numpy as np

REL_TOL = 1e-24
THRESH_PRIMARY = 0.99
THRESH_STRICT = 0.999999
SIGN_FLIP_ENV = "HYPATIAX_R2_SIGN_FLIP"
CATASTROPHIC_FLOOR = -100.0   # r2_scored(): "ok" scores below this become -inf
PRED_ABS_LIMIT = 1e100        # r2_scored(): larger |pred| is a failure


def r2_checked(y_true, y_pred) -> tuple[float, str]:
    """Return (r2, status). Status is one of:
    ok, degenerate_target, nonfinite_target, nonfinite_pred, bad_shape.
    """
    yt = np.asarray(y_true, dtype=float).ravel()
    yp = np.asarray(y_pred, dtype=float).ravel()
    if yt.shape != yp.shape:
        return float("-inf"), "bad_shape"
    if yt.size < 2:
        return float("nan"), "degenerate_target"
    if not np.isfinite(yt).all():
        return float("nan"), "nonfinite_target"
    if not np.isfinite(yp).all():
        return float("-inf"), "nonfinite_pred"

    ss_tot = float(np.sum((yt - yt.mean()) ** 2))
    scale = float(np.sum(yt ** 2))
    if ss_tot <= REL_TOL * max(scale, 1e-300):
        return float("nan"), "degenerate_target"

    ss_res = float(np.sum((yt - yp) ** 2))
    return 1.0 - ss_res / ss_tot, "ok"


def r2(y_true, y_pred) -> float:
    """Float-only wrapper (nan if undefined, -inf if the prediction failed)."""
    return r2_checked(y_true, y_pred)[0]


def sign_flip_enabled() -> bool:
    return os.environ.get(SIGN_FLIP_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def r2_scored(y_true, y_pred, sign_flip: bool | None = None,
              floor: float | None = CATASTROPHIC_FLOOR) -> tuple[float, str]:
    """Benchmark entry point: canonical R^2 plus the benchmarks' robustness
    guards, and the optional legacy sign-flip.

    * ``|pred| > PRED_ABS_LIMIT`` -> (-inf, "pred_out_of_range"): garbage
      numerical output (the "R^2 = -7e12" class seen in PureLLM logs).
    * ``sign_flip=None`` defers to HYPATIAX_R2_SIGN_FLIP (default off); only
      considered for a scorable (status "ok") negative R^2.
    * an "ok" R^2 below ``floor`` -> (-inf, "catastrophic"), so one divergent
      prediction cannot dominate a mean. ``floor=None`` disables this.
    """
    yp = np.asarray(y_pred, dtype=float)
    if yp.size and np.isfinite(yp).all() and np.abs(yp).max() > PRED_ABS_LIMIT:
        return float("-inf"), "pred_out_of_range"
    val, status = r2_checked(y_true, y_pred)
    if sign_flip is None:
        sign_flip = sign_flip_enabled()
    if sign_flip and status == "ok" and val < 0.0:
        flipped, fstatus = r2_checked(y_true, -yp.ravel())
        if fstatus == "ok" and flipped > val:
            val = flipped
    if status == "ok" and floor is not None and val < floor:
        return float("-inf"), "catastrophic"
    return val, status


def is_recovered(r2_value: float, threshold: float = THRESH_PRIMARY) -> bool:
    """True only for a finite R^2 at or above the threshold. nan/-inf -> False."""
    return bool(np.isfinite(r2_value) and r2_value >= threshold)


def selection_score(r2_value: float) -> float:
    """Use when ranking candidates by R^2: undefined scores must lose, not win
    or be silently dropped by NaN comparisons."""
    return float("-inf") if not np.isfinite(r2_value) else float(r2_value)
