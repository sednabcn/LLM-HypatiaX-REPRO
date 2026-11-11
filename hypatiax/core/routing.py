"""Deterministic routing primitives shared by hybrid discovery paths.

The structural-risk rule is intentionally conservative: a trusted formula that
uses a flagged transcendental function cannot take the pure-LLM route. It must
be combined with a finite neural prediction; if that prediction is unavailable,
the route fails closed to the NN fallback (or records no prediction).
"""
from __future__ import annotations

import ast
import re
from typing import Any

import numpy as np

STRUCTURAL_RISK_FUNCTIONS = frozenset({"exp", "log", "Phi", "sin", "cos", "erf"})


def structural_risk_tokens(*sources: str | None) -> list[str]:
    """Return exact flagged function-call names found in Python/formula text.

    Attribute calls such as np.exp, math.sin, and scipy.special.erf are detected.
    Bare variable names or substrings such as 'exponential_rate' are not.
    """
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
                # Conservative fallback for formula fragments that are not valid
                # Python: match a complete function token followed by '('.
                found.update(
                    name for name in STRUCTURAL_RISK_FUNCTIONS
                    if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*\(", source)
                )
                continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in STRUCTURAL_RISK_FUNCTIONS:
                found.add(name)
    return sorted(found)


def select_hypatiax_route(
    fitted_train_r2: float,
    nn_train_r2: float,
    fitted_preds_train: Any,
    nn_preds_train: Any,
    structural_tokens: list[str] | tuple[str, ...] = (),
    trust_threshold: float = 0.5,
) -> dict[str, Any]:
    """Select NN fallback, pure LLM, or ensemble using training-only evidence.

    Existing R²-proportional blending is retained here; the manuscript's
    OOD-calibrated alpha blend is not claimed until its probe/KDE stages exist.
    """
    llm_ok = (
        fitted_preds_train is not None
        and np.asarray(fitted_preds_train).ndim == 1
        and np.asarray(fitted_preds_train).size > 0
        and bool(np.isfinite(np.asarray(fitted_preds_train, dtype=float)).all())
        and np.isfinite(fitted_train_r2)
        and float(fitted_train_r2) >= float(trust_threshold)
    )
    nn_ok = (
        nn_preds_train is not None
        and np.asarray(nn_preds_train).ndim == 1
        and np.asarray(nn_preds_train).size > 0
        and bool(np.isfinite(np.asarray(nn_preds_train, dtype=float)).all())
    )
    if llm_ok and nn_ok and np.asarray(fitted_preds_train).shape != np.asarray(nn_preds_train).shape:
        nn_ok = False

    if not llm_ok:
        return {
            "decision": "nn", "predictions": nn_preds_train if nn_ok else None,
            "route_reason": "trust_gate_failed", "trust_gate_passed": False,
            "structural_risk_flag": bool(structural_tokens),
            "structural_risk_tokens": sorted(set(structural_tokens)),
            "blend_weights": None,
        }

    if structural_tokens:
        if not nn_ok:
            return {
                "decision": "nn", "predictions": None,
                "route_reason": "structural_risk_nn_unavailable",
                "trust_gate_passed": True, "structural_risk_flag": True,
                "structural_risk_tokens": sorted(set(structural_tokens)),
                "blend_weights": None,
            }
        llm_strength = max(float(fitted_train_r2), 0.0)
        nn_strength = max(float(nn_train_r2), 0.0) if np.isfinite(nn_train_r2) else 0.0
        total = llm_strength + nn_strength
        w_llm = llm_strength / total if total > 0 else 0.5
        predictions = w_llm * np.asarray(fitted_preds_train) + (1.0 - w_llm) * np.asarray(nn_preds_train)
        return {
            "decision": "ensemble", "predictions": predictions,
            "route_reason": "structural_risk_precedence", "trust_gate_passed": True,
            "structural_risk_flag": True,
            "structural_risk_tokens": sorted(set(structural_tokens)),
            "blend_weights": {"llm": float(w_llm), "nn": float(1.0 - w_llm)},
        }

    if float(fitted_train_r2) >= 0.95:
        return {
            "decision": "fitted_llm", "predictions": fitted_preds_train,
            "route_reason": "trusted_high_fit_no_structural_risk",
            "trust_gate_passed": True, "structural_risk_flag": False,
            "structural_risk_tokens": [], "blend_weights": None,
        }

    if nn_ok and np.isfinite(nn_train_r2) and float(nn_train_r2) >= 0.5 and abs(float(fitted_train_r2) - float(nn_train_r2)) <= 0.15:
        llm_strength = max(float(fitted_train_r2), 0.0)
        nn_strength = max(float(nn_train_r2), 0.0)
        total = llm_strength + nn_strength
        w_llm = llm_strength / total if total > 0 else 0.5
        predictions = w_llm * np.asarray(fitted_preds_train) + (1.0 - w_llm) * np.asarray(nn_preds_train)
        return {
            "decision": "ensemble", "predictions": predictions,
            "route_reason": "competitive_candidates", "trust_gate_passed": True,
            "structural_risk_flag": False, "structural_risk_tokens": [],
            "blend_weights": {"llm": float(w_llm), "nn": float(1.0 - w_llm)},
        }

    return {
        "decision": "nn", "predictions": nn_preds_train if nn_ok else None,
        "route_reason": "llm_not_high_confidence", "trust_gate_passed": True,
        "structural_risk_flag": False, "structural_risk_tokens": [],
        "blend_weights": None,
    }
