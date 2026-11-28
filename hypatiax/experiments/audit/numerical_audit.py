"""Numerical comparison for trusted callables (never evaluates formula source strings)."""
from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import Any

from .audit_schema import audit_result, NOT_ASSESSABLE, NUMERICALLY_AGREE, NUMERICALLY_DISAGREE


def compare_callables(
    predicted: Callable[..., Any] | None,
    reference: Callable[..., Any] | None,
    points: Iterable[tuple[Any, ...]],
    *,
    rel_tol: float = 1e-9,
    abs_tol: float = 1e-12,
) -> dict[str, Any]:
    """Compare two trusted callables at explicit input points.

    Callables are invoked directly, so callers must only supply trusted functions.
    This utility deliberately does not parse or execute generated Python source.
    """
    if not callable(predicted) or not callable(reference):
        return audit_result(NOT_ASSESSABLE, reason="predicted and reference must be trusted callables")
    if (not isinstance(rel_tol, (int, float)) or not math.isfinite(float(rel_tol))
            or rel_tol < 0 or not isinstance(abs_tol, (int, float))
            or not math.isfinite(float(abs_tol)) or abs_tol < 0):
        return audit_result(NOT_ASSESSABLE, reason="tolerances must be finite non-negative numbers")

    checked = 0
    max_abs_error = 0.0
    max_rel_error = 0.0
    failures: list[dict[str, Any]] = []
    try:
        for point in points:
            if not isinstance(point, tuple):
                point = tuple(point)
            expected = float(reference(*point))
            actual = float(predicted(*point))
            if not math.isfinite(expected) or not math.isfinite(actual):
                failures.append({"point": list(point), "reason": "non-finite output"})
            else:
                abs_error = abs(actual - expected)
                scale = max(abs(actual), abs(expected))
                rel_error = abs_error / scale if scale else 0.0
                max_abs_error = max(max_abs_error, abs_error)
                max_rel_error = max(max_rel_error, rel_error)
                if not math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol):
                    failures.append({
                        "point": list(point), "predicted": actual, "reference": expected,
                        "absolute_error": abs_error,
                    })
            checked += 1
    except Exception as exc:
        return audit_result(
            NOT_ASSESSABLE, checked=checked,
            reason=f"{type(exc).__name__}: {exc}",
        )

    if checked == 0:
        return audit_result(NOT_ASSESSABLE, checked=0, reason="no numerical points supplied")
    return audit_result(
        NUMERICALLY_DISAGREE if failures else NUMERICALLY_AGREE,
        checked=checked,
        max_absolute_error=max_abs_error,
        max_relative_error=max_rel_error,
        failures=failures,
        tolerances={"relative": float(rel_tol), "absolute": float(abs_tol)},
    )
