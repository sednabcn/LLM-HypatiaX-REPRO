"""Training-only Pareto selection and report assembly for symbolic candidates.

This module consumes scientific gate records and fold-validation summaries.
It has no API for far/test observations or evaluation metrics.
"""
from __future__ import annotations

import math
from dataclasses import replace
from typing import Any, Mapping, Sequence

from .discovery_contracts import CandidateRecord, DiscoveryReport
from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _hard_gates_pass(candidate: CandidateRecord) -> bool:
    """Fail closed if any declared hard gate failed or remains unknown."""
    if not candidate.eligible:
        return False
    return all(
        outcome.severity != "hard"
        or outcome.status in {"pass", "not_applicable"}
        for outcome in candidate.constraint_outcomes
    )


def _finite_fold_scores(candidate: CandidateRecord) -> list[float]:
    validation = candidate.metrics.get("training_validation", {})
    if not isinstance(validation, Mapping):
        return []
    folds = validation.get("fold_metrics", ())
    if not isinstance(folds, (tuple, list)):
        return []
    scores: list[float] = []
    for fold in folds:
        if not isinstance(fold, Mapping):
            continue
        value = fold.get("normalized_rmse")
        if isinstance(value, (int, float)) and math.isfinite(float(value)) and value >= 0:
            scores.append(float(value))
    return scores


def _complexity(candidate: CandidateRecord, variable_names: Sequence[str]) -> int | None:
    supplied = candidate.metrics.get("complexity", {})
    if isinstance(supplied, Mapping):
        count = supplied.get("node_count")
        if isinstance(count, int) and count >= 0:
            return count
    try:
        import sympy as sp
        parsed = parse_sympy_expression(
            candidate.normalized_expression or candidate.expression,
            list(variable_names),
        )
        return int(sp.count_ops(parsed, visual=False))
    except Exception:
        return None


def _stability(candidate: CandidateRecord) -> float | None:
    validation = candidate.metrics.get("training_validation", {})
    if not isinstance(validation, Mapping):
        return None
    stability = validation.get("expression_stability", {})
    if not isinstance(stability, Mapping):
        return None
    value = stability.get("dominant_fraction")
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        if 0.0 <= float(value) <= 1.0:
            return float(value)
    return None


def _dominates(left: Mapping[str, float], right: Mapping[str, float]) -> bool:
    """All objectives are minimized; require one strict improvement."""
    keys = ("mean_normalized_rmse", "worst_normalized_rmse", "complexity")
    no_worse = all(left[key] <= right[key] for key in keys)
    strictly_better = any(left[key] < right[key] for key in keys)
    return no_worse and strictly_better


def select_pareto_discovery_report(
    candidates: Sequence[CandidateRecord],
    *,
    variable_names: Sequence[str],
    provenance: Mapping[str, Any] | None = None,
    minimum_valid_folds: int = 2,
) -> DiscoveryReport:
    """Build a report and Pareto front using only declared gates and train folds.

    Required per-candidate metric shape:
      metrics["training_validation"]["fold_metrics"] = [
        {"normalized_rmse": finite_nonnegative_float, ...}, ...
      ]

    The selector never accepts far/test metrics. It ranks eligible candidates
    on mean and worst-fold normalized RMSE plus symbolic operation count.
    Expression recurrence is reported as a diagnostic, not a gate/objective.
    """
    if minimum_valid_folds < 1:
        raise ValueError("minimum_valid_folds must be >= 1")
    records = tuple(candidates)
    if len({item.candidate_id for item in records}) != len(records):
        raise ValueError("candidate IDs must be unique")
    if not records:
        return DiscoveryReport(
            status="no_candidates_generated",
            failure_reasons=("No candidate records were supplied.",),
            provenance=dict(provenance or {}),
        )

    objectives: dict[str, dict[str, float]] = {}
    enriched: list[CandidateRecord] = []
    gate_eligible_count = 0
    for candidate in records:
        metrics = dict(candidate.metrics)
        scores = _finite_fold_scores(candidate)
        node_count = _complexity(candidate, variable_names)
        stable_fraction = _stability(candidate)
        gate_ok = _hard_gates_pass(candidate)
        if gate_ok:
            gate_eligible_count += 1
        enough_evidence = len(scores) >= minimum_valid_folds
        if gate_ok and enough_evidence and node_count is not None:
            objectives[candidate.candidate_id] = {
                "mean_normalized_rmse": sum(scores) / len(scores),
                "worst_normalized_rmse": max(scores),
                "complexity": float(node_count),
            }
        metrics["pareto_selection"] = {
            "hard_gates_passed": gate_ok,
            "valid_normalized_fold_count": len(scores),
            "minimum_valid_folds": minimum_valid_folds,
            "complexity_node_count": node_count,
            "expression_stability_fraction": stable_fraction,
            "eligible_for_pareto": (
                gate_ok and enough_evidence and node_count is not None
            ),
            "objectives": objectives.get(candidate.candidate_id),
        }
        enriched.append(replace(candidate, metrics=metrics))

    if not objectives:
        if gate_eligible_count == 0:
            status = "all_candidates_failed_physical_gates"
            reason = "No candidate passed all declared hard scientific gates."
        else:
            status = "insufficient_validation_evidence"
            reason = (
                "No hard-gate-eligible candidate had sufficient finite training-fold "
                "normalized RMSE evidence and a valid complexity measure."
            )
        return DiscoveryReport(
            status=status,
            candidates=tuple(enriched),
            failure_reasons=(reason,),
            provenance={
                **dict(provenance or {}),
                "selection_policy": "training_only_pareto_v1",
                "selection_data_scope": "training_region_only",
            },
        )

    ids = tuple(objectives)
    pareto_ids = tuple(
        candidate_id for candidate_id in ids
        if not any(
            other_id != candidate_id
            and _dominates(objectives[other_id], objectives[candidate_id])
            for other_id in ids
        )
    )
    # Deterministic recommendation among the Pareto set. Stability is a
    # diagnostic tie-break only; missing stability sorts after measured values.
    selected_candidate = {
        candidate.candidate_id: candidate for candidate in enriched
    }
    selected_id = min(
        pareto_ids,
        key=lambda candidate_id: (
            objectives[candidate_id]["mean_normalized_rmse"],
            objectives[candidate_id]["worst_normalized_rmse"],
            objectives[candidate_id]["complexity"],
            _stability(selected_candidate[candidate_id]) is None,
            -(_stability(selected_candidate[candidate_id]) or 0.0),
            candidate_id,
        ),
    )
    selected = selected_candidate[selected_id]
    has_soft_warning = any(
        outcome.severity == "soft"
        and outcome.status not in {"pass", "not_applicable"}
        for outcome in selected.constraint_outcomes
    )
    return DiscoveryReport(
        status="accepted_with_warnings" if has_soft_warning else "accepted",
        candidates=tuple(enriched),
        selected_candidate_id=selected_id,
        pareto_candidate_ids=pareto_ids,
        provenance={
            **dict(provenance or {}),
            "selection_policy": "training_only_pareto_v1",
            "selection_data_scope": "training_region_only",
            "objectives": [
                "mean_normalized_rmse_min",
                "worst_normalized_rmse_min",
                "symbolic_operation_count_min",
            ],
            "tie_break": [
                "mean_normalized_rmse",
                "worst_normalized_rmse",
                "symbolic_operation_count",
                "expression_stability_fraction_diagnostic",
                "candidate_id",
            ],
            "far_test_data_used_for_selection": False,
        },
    )


__all__ = ["select_pareto_discovery_report"]
