"""Conservative structural matching for independently discovered fold equations.

Numeric coefficients are abstracted while variable identities, operators,
functions, and numeric exponents remain part of the structural signature.
This is a matching heuristic for recurrence evidence, not a proof of
mathematical equivalence.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Iterable

import numpy as np


def canonicalize_symbolic_structure(expression: str, variable_names: Iterable[str]) -> str:
    """Return a deterministic coefficient-abstracted symbolic structure key.

    Parsing uses the restricted AST parser. Rational/algebraic normalization
    is deliberately conservative: it combines arithmetic through SymPy's
    together/cancel pipeline but does not claim arbitrary functional identity.
    Numeric exponents remain structural; other numeric literals are treated as
    fitted coefficients/constants.
    """
    import sympy as sp
    from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression

    names = tuple(variable_names)
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("expression must be a non-empty string")
    parsed = parse_sympy_expression(expression.replace("^", "**"), list(names))
    normalized = sp.cancel(sp.together(parsed))
    exponent_literals = {
        power.exp for power in normalized.atoms(sp.Pow)
        if power.exp.is_number
    }
    numeric_literals = normalized.atoms(sp.Number) - exponent_literals
    coefficient = sp.Symbol("__coefficient__")
    abstracted = normalized.xreplace({value: coefficient for value in numeric_literals})
    return sp.srepr(abstracted)


def match_fold_discovered_structures(
    fold_searches: Iterable[dict],
    fold_metrics: Iterable[dict],
    variable_names: Iterable[str],
    *,
    minimum_recurrence: int = 2,
    minimum_recurrence_fraction: float = 0.5,
) -> dict:
    """Group fold equations by conservative structure and aggregate matched-fold scores.

    Only folds that independently rediscover the same coefficient-abstracted
    structure contribute to that structure's score. Failed/unparseable
    expressions are retained in the unmatched audit. No equations are
    averaged, and the output is explicitly internal training-only evidence.
    """
    searches = list(fold_searches)
    metrics = list(fold_metrics)
    names = tuple(variable_names)
    if minimum_recurrence < 2:
        raise ValueError("minimum_recurrence must be >= 2")
    if not 0.0 < minimum_recurrence_fraction <= 1.0:
        raise ValueError("minimum_recurrence_fraction must be in (0, 1]")

    metric_by_fold = {
        (int(item["repeat"]), int(item["fold"])): item for item in metrics
    }
    grouped: dict[str, list[dict]] = defaultdict(list)
    unmatched: list[dict] = []
    denominator = len(searches)

    for search in searches:
        fold_id = (int(search["repeat"]), int(search["fold"]))
        expression = str(search.get("expression") or "")
        try:
            signature = canonicalize_symbolic_structure(expression, names)
        except Exception as exc:
            unmatched.append({
                "repeat": fold_id[0], "fold": fold_id[1],
                "expression": expression,
                "reason": f"{type(exc).__name__}: {exc}"[:300],
            })
            continue
        metric = metric_by_fold.get(fold_id)
        if metric is None:
            unmatched.append({
                "repeat": fold_id[0], "fold": fold_id[1],
                "expression": expression,
                "reason": "missing_fold_metric",
            })
            continue
        grouped[signature].append({
            "repeat": fold_id[0],
            "fold": fold_id[1],
            "expression": expression,
            "normalized_rmse": metric.get("normalized_rmse"),
            "rmse": metric.get("rmse"),
            "validation_size": metric.get("validation_size"),
        })

    structures = []
    for signature, members in grouped.items():
        values = np.asarray([
            float(item["normalized_rmse"])
            for item in members
            if item.get("normalized_rmse") is not None
            and np.isfinite(float(item["normalized_rmse"]))
            and float(item["normalized_rmse"]) >= 0
        ], dtype=float)
        recurrence = len(members)
        fraction = recurrence / denominator if denominator else 0.0
        eligible = (
            recurrence >= minimum_recurrence
            and fraction >= minimum_recurrence_fraction
            and values.size == recurrence
        )
        structures.append({
            "structure_id": hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16],
            "canonical_structure": signature,
            "recurrence_count": recurrence,
            "recurrence_fraction": fraction,
            "eligible": bool(eligible),
            "folds": members,
            "mean_normalized_rmse": float(np.mean(values)) if values.size else None,
            "worst_normalized_rmse": float(np.max(values)) if values.size else None,
            "normalized_rmse_std": float(np.std(values)) if values.size else None,
            "score_fold_count": int(values.size),
            "selection_scope": "internal_training_folds_only",
        })

    structures.sort(key=lambda item: (
        not item["eligible"],
        item["mean_normalized_rmse"] if item["mean_normalized_rmse"] is not None else float("inf"),
        -item["recurrence_count"],
        item["structure_id"],
    ))
    return {
        "status": "matched_structures" if any(item["eligible"] for item in structures)
                  else "NO_RECURRENT_CANDIDATE",
        "matching_policy": "restricted_sympy_normalization_with_numeric_coefficients_abstracted",
        "equivalence_claim": False,
        "fold_count": denominator,
        "minimum_recurrence": minimum_recurrence,
        "minimum_recurrence_fraction": minimum_recurrence_fraction,
        "structures": structures,
        "unmatched_folds": unmatched,
        "far_test_data_used": False,
    }


__all__ = ["canonicalize_symbolic_structure", "match_fold_discovered_structures"]
