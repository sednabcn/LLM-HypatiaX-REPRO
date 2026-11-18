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


def _stability(
    candidate: CandidateRecord, minimum_expression_count: int
) -> float | None:
    validation = candidate.metrics.get("training_validation", {})
    if not isinstance(validation, Mapping):
        return None
    stability = validation.get("expression_stability", {})
    if not isinstance(stability, Mapping) or stability.get("status") != "measured":
        return None
    count = stability.get("expression_count")
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or count < minimum_expression_count
    ):
        return None
    value = stability.get("dominant_fraction")
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and 0.0 <= float(value) <= 1.0
    ):
        return float(value)
    return None



def _soft_constraint_violation(candidate: CandidateRecord, constraint_ids: Sequence[str]) -> float | None:
    """Equal-weight mean of complete declared soft-constraint violation fractions."""
    if not constraint_ids:
        return None
    selected = [item for item in candidate.constraint_outcomes if item.constraint_id in set(constraint_ids)]
    if len(selected) != len(constraint_ids):
        return None
    by_id = {item.constraint_id: item for item in selected}
    if set(by_id) != set(constraint_ids):
        return None
    fractions: list[float] = []
    for constraint_id in constraint_ids:
        outcome = by_id[constraint_id]
        if outcome.severity != "soft" or outcome.status not in {"pass", "fail"}:
            return None
        evidence = outcome.evidence
        count, violations, fraction = evidence.get("evaluation_count"), evidence.get("violation_count"), evidence.get("violation_fraction")
        if (isinstance(count, bool) or not isinstance(count, int) or count <= 0
            or isinstance(violations, bool) or not isinstance(violations, int)
            or not 0 <= violations <= count or isinstance(fraction, bool)
            or not isinstance(fraction, (int, float)) or not math.isfinite(float(fraction))
            or not 0.0 <= float(fraction) <= 1.0
            or not math.isclose(float(fraction), violations / count, rel_tol=1e-9, abs_tol=1e-12)
            or ((outcome.status == "pass") != (violations == 0))):
            return None
        fractions.append(float(fraction))
    return sum(fractions) / len(fractions)

def _dominates(left: Mapping[str, float], right: Mapping[str, float]) -> bool:
    """All objectives are minimized; require one strict improvement."""
    keys = tuple(left.keys())
    if set(keys) != set(right.keys()):
        raise ValueError("Pareto candidates must expose the same objective vector")
    no_worse = all(left[key] <= right[key] for key in keys)
    strictly_better = any(left[key] < right[key] for key in keys)
    return no_worse and strictly_better


def select_pareto_discovery_report(
    candidates: Sequence[CandidateRecord],
    *,
    variable_names: Sequence[str],
    provenance: Mapping[str, Any] | None = None,
    minimum_valid_folds: int = 2,
    require_nested_structure_evidence: bool = False,
    soft_constraint_ids: Sequence[str] = (),
) -> DiscoveryReport:
    """Build a report and Pareto front using only declared gates and train folds.

    Required per-candidate metric shape:
      metrics["training_validation"]["fold_metrics"] = [
        {"normalized_rmse": finite_nonnegative_float, ...}, ...
      ]

    The selector never accepts far/test metrics. It ranks eligible candidates
    on mean and worst-fold normalized RMSE plus symbolic operation count.
    When require_nested_structure_evidence is true, a candidate must also have
    a unique recurrent-structure crosswalk from fresh fold-local searches.
    That crosswalk is a separate evidence gate, not a copied fixed-structure score.
    """
    if minimum_valid_folds < 1:
        raise ValueError("minimum_valid_folds must be >= 1")
    declared_soft_ids = tuple(soft_constraint_ids)
    if len(set(declared_soft_ids)) != len(declared_soft_ids) or any(not isinstance(item, str) or not item.strip() for item in declared_soft_ids):
        raise ValueError("soft_constraint_ids must be unique non-empty strings")
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
        stable_fraction = _stability(candidate, minimum_valid_folds)
        soft_violation = _soft_constraint_violation(candidate, declared_soft_ids)
        gate_ok = _hard_gates_pass(candidate)
        if gate_ok:
            gate_eligible_count += 1
        enough_evidence = len(scores) >= minimum_valid_folds
        nested = metrics.get("nested_structure_evidence", {})
        nested_ok = (
            isinstance(nested, Mapping)
            and nested.get("status") == "matched_candidate_structure"
            and nested.get("candidate_specific_nested_evidence") is True
            and nested.get("far_test_data_used") is False
        )
        nested_required_ok = (not require_nested_structure_evidence) or nested_ok
        eligibility_reasons = list(candidate.rejection_reasons)
        if not candidate.eligible and not eligibility_reasons:
            eligibility_reasons.append("candidate_marked_ineligible")
        for outcome in candidate.constraint_outcomes:
            if outcome.severity == "hard" and outcome.status not in {"pass", "not_applicable"}:
                eligibility_reasons.append(
                    f"hard_constraint_{outcome.status}:{outcome.constraint_id}"
                )
        if not enough_evidence:
            eligibility_reasons.append("insufficient_valid_training_folds")
        validation = metrics.get("training_validation", {})
        raw_fold_metrics = (
            validation.get("fold_metrics", ())
            if isinstance(validation, Mapping) else ()
        )
        if isinstance(raw_fold_metrics, (tuple, list)) and len(scores) < len(raw_fold_metrics):
            eligibility_reasons.append("missing_or_nonfinite_normalized_fold_scores")
        if node_count is None:
            eligibility_reasons.append("symbolic_complexity_unavailable")
        if stable_fraction is None:
            eligibility_reasons.append("expression_stability_unavailable")
        if declared_soft_ids and soft_violation is None:
            eligibility_reasons.append("soft_constraint_evidence_incomplete")
        if require_nested_structure_evidence and not nested_ok:
            eligibility_reasons.append("required_nested_structure_evidence_not_matched")
        eligibility_reasons = list(dict.fromkeys(eligibility_reasons))
        pareto_eligible = not eligibility_reasons
        if pareto_eligible:
            objectives[candidate.candidate_id] = {
                "mean_normalized_rmse": sum(scores) / len(scores),
                "worst_normalized_rmse": max(scores),
                "complexity": float(node_count),
                # Minimize the negative fraction, i.e. maximize recurrence.
                "negative_expression_stability": -float(stable_fraction),
                **({"mean_soft_constraint_violation_fraction": float(soft_violation)} if declared_soft_ids else {}),
            }
        metrics["pareto_selection"] = {
            "hard_gates_passed": gate_ok,
            "valid_normalized_fold_count": len(scores),
            "minimum_valid_folds": minimum_valid_folds,
            "complexity_node_count": node_count,
            "expression_stability_fraction": stable_fraction,
            "declared_soft_constraint_ids": list(declared_soft_ids),
            "mean_soft_constraint_violation_fraction": soft_violation,
            "nested_structure_evidence_required": require_nested_structure_evidence,
            "nested_structure_evidence_passed": nested_ok,
            "eligible_for_pareto": pareto_eligible,
            "eligibility_reasons": eligibility_reasons,
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
                "normalized RMSE evidence, a valid complexity measure, and all "
                "required nested-structure evidence."
            )
        return DiscoveryReport(
            status=status,
            candidates=tuple(enriched),
            failure_reasons=(reason,),
            provenance={
                **dict(provenance or {}),
                "selection_policy": (
                    ("training_only_pareto_v6_nested_structure_soft_constraints" if require_nested_structure_evidence and declared_soft_ids else "training_only_pareto_v5_soft_constraints" if declared_soft_ids else "training_only_pareto_v4_nested_structure_stability" if require_nested_structure_evidence else "training_only_pareto_v3_stability")
                ),
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
    # All scientific objectives are represented in the Pareto front.
    # This deterministic tie-break only resolves exact objective ties.
    selected_candidate = {
        candidate.candidate_id: candidate for candidate in enriched
    }
    selected_id = min(
        pareto_ids,
        key=lambda candidate_id: (
            objectives[candidate_id]["mean_normalized_rmse"],
            objectives[candidate_id]["worst_normalized_rmse"],
            objectives[candidate_id]["complexity"],
            objectives[candidate_id].get("mean_soft_constraint_violation_fraction", 0.0),
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
            "selection_policy": (
                ("training_only_pareto_v6_nested_structure_soft_constraints" if require_nested_structure_evidence and declared_soft_ids else "training_only_pareto_v5_soft_constraints" if declared_soft_ids else "training_only_pareto_v4_nested_structure_stability" if require_nested_structure_evidence else "training_only_pareto_v3_stability")
            ),
            "selection_data_scope": "training_region_only",
            "objectives": [
                "mean_normalized_rmse_min",
                "worst_normalized_rmse_min",
                "symbolic_operation_count_min",
                "expression_stability_fraction_max",
                *(["mean_declared_soft_constraint_violation_fraction_min"] if declared_soft_ids else []),
            ],
            "tie_break": [
                "mean_normalized_rmse",
                "worst_normalized_rmse",
                "symbolic_operation_count",
                "mean_declared_soft_constraint_violation_fraction",
                "candidate_id",
            ],
            "far_test_data_used_for_selection": False,
            "nested_structure_evidence_required": require_nested_structure_evidence,
            "nested_structure_evidence_role": "candidate_specific_recurrence_gate" if require_nested_structure_evidence else "optional_audit",
            "soft_constraint_ids": list(declared_soft_ids),
            "soft_constraint_aggregation": "unweighted_mean_of_declared_violation_fractions" if declared_soft_ids else "disabled",
        },
    )


__all__ = ["select_pareto_discovery_report"]
