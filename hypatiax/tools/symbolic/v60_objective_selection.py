"""V60 objective evidence and deterministic selection from training-fold audits.

The selector accepts only normalized proposals, declared-gate outcomes, and
completed training-only fold evidence. It has no training arrays or far-set
argument. All objectives are independently recomputed from the serialized
fold evidence and restricted symbolic expression parser.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any, Mapping, Sequence

import sympy as sp

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _verify_fold(record: Mapping[str, Any], expected_fold_count: int) -> tuple[list[float], list[float]]:
    folds = record.get("folds")
    if not isinstance(folds, list) or len(folds) != expected_fold_count or expected_fold_count < 2:
        raise ValueError("candidate must contain the complete declared fold set")
    scores_rmse: list[float] = []
    scores_nrmse: list[float] = []
    seen_fold_ids: set[int] = set()
    for fold in folds:
        if not isinstance(fold, Mapping):
            raise ValueError("fold evidence must be a mapping")
        fold_id = fold.get("fold")
        if isinstance(fold_id, bool) or not isinstance(fold_id, int) or fold_id in seen_fold_ids:
            raise ValueError("fold identifiers must be unique integers")
        seen_fold_ids.add(fold_id)
        train = fold.get("training_row_indices")
        validation = fold.get("validation_row_indices")
        if not isinstance(train, list) or not isinstance(validation, list) or not train or not validation:
            raise ValueError("fold row-index evidence is missing")
        if any(isinstance(i, bool) or not isinstance(i, int) or i < 0 for i in train + validation):
            raise ValueError("fold row indices must be non-negative integers")
        if len(set(train)) != len(train) or len(set(validation)) != len(validation):
            raise ValueError("fold row indices must be unique")
        if set(train).intersection(validation):
            raise ValueError("fold training and validation rows overlap")
        if fold.get("training_row_count") != len(train) or fold.get("validation_row_count") != len(validation):
            raise ValueError("fold row counts do not match row-index evidence")
        rmse = _finite_number(fold.get("validation_rmse"), "validation_rmse")
        if rmse < 0:
            raise ValueError("validation_rmse cannot be negative")
        scores_rmse.append(rmse)
        nrmse = fold.get("validation_nrmse")
        if nrmse is None:
            scores_nrmse.append(float("nan"))
        else:
            normalized = _finite_number(nrmse, "validation_nrmse")
            if normalized < 0:
                raise ValueError("validation_nrmse cannot be negative")
            scores_nrmse.append(normalized)
        for coefficient_name in ("scale", "intercept"):
            _finite_number(fold.get("coefficients", {}).get(coefficient_name), f"fold coefficient {coefficient_name}")
    if seen_fold_ids != set(range(expected_fold_count)):
        raise ValueError("fold identifiers must be contiguous from zero")
    return scores_rmse, scores_nrmse


def select_native_candidates_from_training_evidence(
    candidates: Sequence[Mapping[str, Any]],
    gate_audit: Mapping[str, Any],
    validation_audit: Mapping[str, Any],
    *,
    variable_names: Sequence[str],
    max_candidates: int = 100,
    max_search_attempts: int = 100,
) -> dict[str, Any]:
    """Verify and Pareto-select eligible candidates using training-fold evidence."""
    for name, value in (("max_candidates", max_candidates), ("max_search_attempts", max_search_attempts)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if gate_audit.get("gate_status") != "completed" or gate_audit.get("training_or_far_data_used") is not False:
        raise ValueError("completed data-independent gate audit is required")
    if validation_audit.get("validation_method") != "training_only_refit_cross_validation":
        raise ValueError("training-only cross-validation evidence is required")
    if validation_audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("validation evidence must explicitly exclude far/evaluation data")
    if validation_audit.get("validation_status") != "completed":
        return {
            "schema": "v60_native_objective_selection_v1",
            "selection_status": "insufficient_validation_evidence",
            "reason": "training validation did not complete",
            "selection_performed": False, "far_or_evaluation_data_used": False,
            "objective_evidence": [], "pareto_candidate_ids": [], "selected_candidate_id": None,
        }

    gate_records = gate_audit.get("candidate_gates")
    validation_records = validation_audit.get("candidate_validation")
    if not isinstance(gate_records, list) or not isinstance(validation_records, list):
        raise ValueError("gate and validation candidate records must be lists")
    eligible_ids = {
        item.get("native_candidate_id") for item in gate_records
        if isinstance(item, Mapping) and item.get("eligible") is True
        and item.get("gate_execution") == "completed"
    }
    proposal_by_id: dict[str, Mapping[str, Any]] = {}
    for item in candidates:
        candidate_id = item.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in proposal_by_id:
            raise ValueError("normalized candidate IDs must be unique non-empty strings")
        proposal_by_id[candidate_id] = item

    expected_folds = validation_audit.get("fold_count")
    training_row_count = validation_audit.get("training_row_count")
    if isinstance(training_row_count, bool) or not isinstance(training_row_count, int) or training_row_count < 1:
        raise ValueError("validation audit must declare its training row count")
    if isinstance(expected_folds, bool) or not isinstance(expected_folds, int) or expected_folds < 2:
        raise ValueError("validation audit must declare at least two folds")
    validation_by_id: dict[str, Mapping[str, Any]] = {}
    for item in validation_records:
        candidate_id = item.get("candidate_id")
        if not isinstance(candidate_id, str) or candidate_id in validation_by_id:
            raise ValueError("validation candidate IDs must be unique strings")
        validation_by_id[candidate_id] = item

    eligible_validated = [
        candidate_id for candidate_id in validation_by_id
        if candidate_id in eligible_ids and candidate_id in proposal_by_id
        and validation_by_id[candidate_id].get("validation_status") == "validated"
    ]
    eligible_validated_count = len(eligible_validated)
    cap = min(eligible_validated_count, max_candidates, max_search_attempts)
    eligible_validated = eligible_validated[:cap]
    raw_evidence: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for candidate_id in eligible_validated:
        proposal = proposal_by_id[candidate_id]
        validation = validation_by_id[candidate_id]
        expression = proposal.get("normalized_expression") or proposal.get("expression")
        try:
            if validation.get("expression") != expression:
                raise ValueError("validation expression does not match normalized proposal")
            parsed = parse_sympy_expression(expression, list(variable_names))
            complexity = int(sp.count_ops(parsed))
            rmse_scores, nrmse_scores = _verify_fold(validation, expected_folds)
            for fold in validation["folds"]:
                if any(index >= training_row_count for index in fold["training_row_indices"] + fold["validation_row_indices"]):
                    raise ValueError("fold row index exceeds declared training row count")
            raw_evidence.append({
                "candidate_id": candidate_id, "expression": expression,
                "producer_provenance": [dict(x) for x in proposal.get("producer_provenance", []) if isinstance(x, Mapping)],
                "complexity": complexity,
                "mean_validation_rmse": float(sum(rmse_scores) / len(rmse_scores)),
                "std_validation_rmse": float((sum((x - sum(rmse_scores) / len(rmse_scores)) ** 2 for x in rmse_scores) / len(rmse_scores)) ** 0.5),
                "mean_validation_nrmse": (
                    float(sum(nrmse_scores) / len(nrmse_scores))
                    if all(math.isfinite(x) for x in nrmse_scores) else None
                ),
                "std_validation_nrmse": (
                    float((sum((x - sum(nrmse_scores) / len(nrmse_scores)) ** 2 for x in nrmse_scores) / len(nrmse_scores)) ** 0.5)
                    if all(math.isfinite(x) for x in nrmse_scores) else None
                ),
                "fold_count": expected_folds,
                "objective_source": "recomputed_from_training_only_fold_evidence",
            })
        except Exception as exc:
            rejected.append({"candidate_id": candidate_id, "reason": f"{type(exc).__name__}: {exc}"})

    if not raw_evidence:
        return {
            "schema": "v60_native_objective_selection_v1",
            "selection_status": "no_credible_candidate",
            "selection_performed": True, "far_or_evaluation_data_used": False,
            "objective_evidence": [], "rejected_candidates": rejected,
            "pareto_candidate_ids": [], "selected_candidate_id": None,
            "budget_truncated_count": eligible_validated_count - cap,
        }

    metric = "mean_validation_nrmse" if all(item["mean_validation_nrmse"] is not None for item in raw_evidence) else "mean_validation_rmse"
    variability = "std_validation_nrmse" if metric.endswith("nrmse") else "std_validation_rmse"
    for item in raw_evidence:
        item["primary_error_objective"] = metric
        item["objectives"] = {
            metric: item[metric],
            variability: item[variability],
            "symbolic_complexity": item["complexity"],
        }
        canonical = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
        item["objective_evidence_sha256"] = sha256(canonical.encode("utf-8")).hexdigest()

    def dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        a, b = left["objectives"], right["objectives"]
        keys = (metric, variability, "symbolic_complexity")
        return all(a[key] <= b[key] for key in keys) and any(a[key] < b[key] for key in keys)

    pareto = [
        item for item in raw_evidence
        if not any(other["candidate_id"] != item["candidate_id"] and dominates(other, item) for other in raw_evidence)
    ]
    pareto.sort(key=lambda item: (
        item["objectives"][metric], item["objectives"]["symbolic_complexity"],
        item["objectives"][variability], item["candidate_id"],
    ))
    selected = pareto[0]
    return {
        "schema": "v60_native_objective_selection_v1",
        "selection_status": "selected",
        "selection_method": "verified_training_evidence_pareto_then_deterministic_tiebreak",
        "primary_error_objective": metric,
        "objective_directions": {metric: "minimize", variability: "minimize", "symbolic_complexity": "minimize"},
        "selection_performed": True,
        "far_or_evaluation_data_used": False,
        "input_eligible_validated_candidate_count": eligible_validated_count,
        "objective_candidate_count": len(raw_evidence),
        "rejected_candidate_count": len(rejected),
        "budget_truncated_count": eligible_validated_count - cap,
        "objective_evidence": raw_evidence,
        "rejected_candidates": rejected,
        "pareto_candidate_ids": [item["candidate_id"] for item in pareto],
        "selected_candidate_id": selected["candidate_id"],
        "selected_expression": selected["expression"],
        "selected_objective_evidence_sha256": selected["objective_evidence_sha256"],
    }


__all__ = ["select_native_candidates_from_training_evidence"]
