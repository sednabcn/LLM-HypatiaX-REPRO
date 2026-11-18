"""Evidence-gated Pareto selection for native V60 joint multi-basis groups.

This selector is deliberately separate from the single-basis selector. It
accepts no observations or far-set arrays: every eligible group's fold
evidence must first be independently recomputed and fingerprinted by the
multi-basis verifier.
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


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _group_id(candidate_ids: Sequence[str]) -> str:
    return "v60mb_" + sha256(
        json.dumps(list(candidate_ids), separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]


def _complexity(expressions: Sequence[str], variable_names: Sequence[str]) -> int:
    parsed = [parse_sympy_expression(expression, list(variable_names)) for expression in expressions]
    # Count operators inside each basis plus the additions joining the terms
    # and the final intercept. This measures the declared additive model form.
    return int(sum(sp.count_ops(item) for item in parsed) + len(expressions))


def select_native_multi_basis_candidates_from_verified_evidence(
    candidates: Sequence[Mapping[str, Any]],
    gate_audit: Mapping[str, Any],
    fit_audit: Mapping[str, Any],
    validation_audit: Mapping[str, Any],
    evidence_audit: Mapping[str, Any],
    *,
    variable_names: Sequence[str],
    max_groups: int = 100,
    max_search_attempts: int = 100,
) -> dict[str, Any]:
    """Select complete, independently verified joint-basis groups.

    The objective is validation error (NRMSE when available for every eligible
    group, otherwise RMSE), fold-to-fold variability, and symbolic complexity.
    All objectives are minimized. The selector verifies evidence fingerprints
    and all group/candidate/lineage references before Pareto construction.
    """
    for name, value in (("max_groups", max_groups), ("max_search_attempts", max_search_attempts)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if not isinstance(variable_names, (list, tuple)) or not variable_names or any(
        not isinstance(name, str) or not name for name in variable_names
    ):
        raise ValueError("variable_names must be a non-empty sequence of names")
    if gate_audit.get("gate_status") != "completed" or gate_audit.get("training_or_far_data_used") is not False:
        raise ValueError("completed data-independent candidate gate audit is required")
    if fit_audit.get("schema") != "v60_native_multi_basis_fits_v1" or fit_audit.get("selection_performed") is not False:
        raise ValueError("audit-only native multi-basis fitting evidence is required")
    if fit_audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("multi-basis fit audit must exclude far/evaluation data")
    if validation_audit.get("schema") != "v60_native_multi_basis_validation_v1":
        raise ValueError("unsupported multi-basis validation schema")
    if validation_audit.get("selection_performed") is not False or validation_audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("validation audit must be training-only and selection-free")
    if validation_audit.get("validation_method") != "training_only_joint_multi_basis_refit_cross_validation":
        raise ValueError("joint multi-basis training-only fold validation is required")
    if evidence_audit.get("schema") != "v60_native_multi_basis_evidence_verification_v1":
        raise ValueError("unsupported multi-basis evidence-verification schema")
    if evidence_audit.get("selection_performed") is not False or evidence_audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("verified evidence must explicitly exclude selection and far/evaluation data")
    if evidence_audit.get("verification_status") not in {"completed", "partial_or_rejected"}:
        raise ValueError("multi-basis evidence verification did not complete")

    training_rows = validation_audit.get("training_row_count")
    fold_count = validation_audit.get("fold_count")
    if isinstance(training_rows, bool) or not isinstance(training_rows, int) or training_rows < 1:
        raise ValueError("validation audit must declare a positive training row count")
    if isinstance(fold_count, bool) or not isinstance(fold_count, int) or fold_count < 2:
        raise ValueError("validation audit must declare at least two folds")

    proposal_by_id: dict[str, Mapping[str, Any]] = {}
    for item in candidates:
        if not isinstance(item, Mapping):
            raise ValueError("normalized candidate proposals must be mappings")
        candidate_id = item.get("candidate_id")
        expression = item.get("normalized_expression") or item.get("expression")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in proposal_by_id:
            raise ValueError("normalized candidate IDs must be unique non-empty strings")
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("normalized candidate expressions must be non-empty strings")
        proposal_by_id[candidate_id] = item

    gate_records = gate_audit.get("candidate_gates")
    fit_records = fit_audit.get("fitted_candidate_groups")
    validation_records = validation_audit.get("candidate_group_validation")
    verified_records = evidence_audit.get("verified_candidate_groups")
    if not all(isinstance(value, list) for value in (gate_records, fit_records, validation_records, verified_records)):
        raise ValueError("gate, fit, validation, and verified group records must be lists")

    eligible_ids = {
        item.get("native_candidate_id")
        for item in gate_records
        if isinstance(item, Mapping) and item.get("eligible") is True and item.get("gate_execution") == "completed"
    }
    fit_by_id: dict[str, Mapping[str, Any]] = {}
    for record in fit_records:
        if not isinstance(record, Mapping):
            raise ValueError("fitted group records must be mappings")
        gid = record.get("candidate_group_id")
        if not isinstance(gid, str) or not gid or gid in fit_by_id:
            raise ValueError("fitted group IDs must be unique non-empty strings")
        fit_by_id[gid] = record
    validation_by_id: dict[str, Mapping[str, Any]] = {}
    for record in validation_records:
        if not isinstance(record, Mapping):
            raise ValueError("validation group records must be mappings")
        gid = record.get("candidate_group_id")
        if not isinstance(gid, str) or not gid or gid in validation_by_id:
            raise ValueError("validation group IDs must be unique non-empty strings")
        validation_by_id[gid] = record
    verified_by_id: dict[str, Mapping[str, Any]] = {}
    for record in verified_records:
        if not isinstance(record, Mapping):
            raise ValueError("verified group records must be mappings")
        gid = record.get("candidate_group_id")
        if not isinstance(gid, str) or not gid or gid in verified_by_id:
            raise ValueError("verified group IDs must be unique non-empty strings")
        verified_by_id[gid] = record

    input_count = len(validation_records)
    cap = min(input_count, max_groups, max_search_attempts)
    if evidence_audit.get("input_group_count") != input_count:
        raise ValueError("verifier input group count does not match validation evidence")
    if evidence_audit.get("attempted_group_count") != cap:
        raise ValueError("verifier attempted group count does not match the shared selection budget")
    if evidence_audit.get("budget_truncated_count") != input_count - cap:
        raise ValueError("verifier budget accounting does not reproduce")
    ordered_ids = [record.get("candidate_group_id") for record in validation_records[:cap]]
    raw_evidence: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for group_id in ordered_ids:
        validation = validation_by_id.get(group_id)
        verified = verified_by_id.get(group_id)
        fit = fit_by_id.get(group_id)
        try:
            if validation is None or verified is None or fit is None:
                raise ValueError("group is missing fit, validation, or independent verification evidence")
            if validation.get("validation_status") != "validated":
                raise ValueError("only fully validated groups are eligible")
            if fit.get("fit_status") != "fitted":
                raise ValueError("group does not have a completed joint fit")
            if verified.get("verification_status") != "verified":
                raise ValueError("group evidence was not independently verified")

            ids = validation.get("basis_candidate_ids")
            expressions = validation.get("basis_expressions")
            if not isinstance(ids, list) or not 2 <= len(ids) <= 3 or len(set(ids)) != len(ids):
                raise ValueError("basis candidate IDs must be a unique list of two or three IDs")
            if not isinstance(expressions, list) or len(expressions) != len(ids):
                raise ValueError("basis expressions must align with candidate IDs")
            if group_id != _group_id(ids):
                raise ValueError("group ID does not match ordered basis candidate IDs")
            if fit.get("basis_candidate_ids") != ids or fit.get("basis_expressions") != expressions:
                raise ValueError("fit group identity does not match validation group")
            if verified.get("basis_candidate_ids") != ids or verified.get("basis_expressions") != expressions:
                raise ValueError("verified group identity does not match validation group")

            expected_lineage = []
            for candidate_id, expression in zip(ids, expressions):
                proposal = proposal_by_id.get(candidate_id)
                if proposal is None or candidate_id not in eligible_ids:
                    raise ValueError("every basis must reference a normalized, gate-eligible candidate")
                actual_expression = proposal.get("normalized_expression") or proposal.get("expression")
                if actual_expression != expression:
                    raise ValueError("basis expression does not match normalized candidate")
                producer_records = proposal.get("producer_provenance", [])
                if not isinstance(producer_records, (list, tuple)):
                    raise ValueError("candidate producer provenance must be a sequence")
                if any(not isinstance(item, Mapping) for item in producer_records):
                    raise ValueError("candidate producer provenance entries must be mappings")
                expected_lineage.extend(dict(item) for item in producer_records)
            if validation.get("source_provenance") != expected_lineage:
                raise ValueError("validation producer lineage does not match normalized proposals")
            if fit.get("source_provenance") != expected_lineage or verified.get("source_provenance") != expected_lineage:
                raise ValueError("fit/verified producer lineage does not match normalized proposals")

            folds = verified.get("verified_folds")
            if not isinstance(folds, list) or len(folds) != fold_count or verified.get("verified_fold_count") != fold_count:
                raise ValueError("verified fold evidence is incomplete")
            if validation.get("fold_count") != fold_count:
                raise ValueError("validation group fold count is incomplete")
            if validation.get("split_strategy") != validation_audit.get("split_strategy"):
                raise ValueError("validation group split strategy does not match the audit")
            validation_folds = validation.get("folds")
            if not isinstance(validation_folds, list) or len(validation_folds) != fold_count:
                raise ValueError("serialized validation fold evidence is incomplete")
            if verified.get("objective_evidence") is None or not isinstance(verified.get("objective_evidence"), Mapping):
                raise ValueError("verified objective evidence is missing")

            for index, (fold, verified_fold) in enumerate(zip(validation_folds, folds)):
                if not isinstance(fold, Mapping) or not isinstance(verified_fold, Mapping):
                    raise ValueError("fold evidence records must be mappings")
                if fold.get("fold") != index or verified_fold.get("fold") != index:
                    raise ValueError("fold IDs must be contiguous and ordered")
                train_idx = fold.get("training_row_indices")
                valid_idx = fold.get("validation_row_indices")
                if not isinstance(train_idx, list) or not isinstance(valid_idx, list):
                    raise ValueError("raw fold row indices must be lists")
                if any(isinstance(value, bool) or not isinstance(value, int) for value in train_idx + valid_idx):
                    raise ValueError("raw fold row indices must be integers, not booleans or floats")
                if verified_fold.get("training_row_indices") != train_idx or verified_fold.get("validation_row_indices") != valid_idx:
                    raise ValueError("verified row indices do not match validation evidence")
                if any(value < 0 or value >= training_rows for value in train_idx + valid_idx):
                    raise ValueError("fold row index is outside the declared training rows")
                for key, verified_key in (
                    ("validation_rmse", "recomputed_rmse"),
                    ("validation_nrmse", "recomputed_nrmse"),
                    ("validation_r2", "recomputed_r2"),
                ):
                    supplied = fold.get(key)
                    recomputed = verified_fold.get(verified_key)
                    if supplied is None or recomputed is None:
                        if supplied is not recomputed:
                            raise ValueError(f"fold {index} {key} differs from verified evidence")
                    elif not math.isclose(_finite_number(supplied, key), _finite_number(recomputed, verified_key), rel_tol=1e-10, abs_tol=1e-12):
                        raise ValueError(f"fold {index} {key} differs from verified evidence")

            objective = verified["objective_evidence"]
            rmse_mean = _finite_number(objective.get("validation_rmse_mean"), "validation_rmse_mean")
            rmse_std = _finite_number(objective.get("validation_rmse_std"), "validation_rmse_std")
            if rmse_mean < 0 or rmse_std < 0:
                raise ValueError("RMSE objectives cannot be negative")
            nrmse_mean = objective.get("validation_nrmse_mean")
            nrmse_std = objective.get("validation_nrmse_std")
            if (nrmse_mean is None) != (nrmse_std is None):
                raise ValueError("normalized error mean/std nullability must match")
            if nrmse_mean is not None:
                nrmse_mean = _finite_number(nrmse_mean, "validation_nrmse_mean")
                nrmse_std = _finite_number(nrmse_std, "validation_nrmse_std")
                if nrmse_mean < 0 or nrmse_std < 0:
                    raise ValueError("normalized error objectives cannot be negative")

            fingerprint_payload = {
                "candidate_group_id": group_id,
                "basis_candidate_ids": ids,
                "basis_expressions": expressions,
                "source_provenance": expected_lineage,
                "folds": folds,
                "aggregates": dict(objective),
                "training_row_count": training_rows,
                "variable_names": list(variable_names),
                "split_strategy": validation.get("split_strategy"),
            }
            if not isinstance(verified.get("evidence_fingerprint"), str) or _digest(fingerprint_payload) != verified.get("evidence_fingerprint"):
                raise ValueError("independent evidence fingerprint does not reproduce")

            complexity = _complexity(expressions, variable_names)
            raw_evidence.append({
                "candidate_group_id": group_id,
                "basis_candidate_ids": list(ids),
                "basis_expressions": list(expressions),
                "source_provenance": expected_lineage,
                "evidence_fingerprint": verified["evidence_fingerprint"],
                "fold_count": fold_count,
                "mean_validation_rmse": rmse_mean,
                "std_validation_rmse": rmse_std,
                "mean_validation_nrmse": nrmse_mean,
                "std_validation_nrmse": nrmse_std,
                "symbolic_complexity": complexity,
                "objective_source": "independently_verified_training_only_joint_fold_evidence",
            })
        except Exception as exc:
            rejected.append({"candidate_group_id": str(group_id), "reason": f"{type(exc).__name__}: {exc}"})

    if not raw_evidence:
        return {
            "schema": "v60_native_multi_basis_objective_selection_v1",
            "selection_status": "no_credible_candidate",
            "selection_method": "verified_joint_basis_training_evidence_pareto",
            "selection_performed": True,
            "far_or_evaluation_data_used": False,
            "input_group_count": input_count,
            "objective_group_count": 0,
            "rejected_group_count": len(rejected),
            "budget_truncated_count": input_count - cap,
            "objective_evidence": [],
            "rejected_candidate_groups": rejected,
            "pareto_candidate_group_ids": [],
            "selected_candidate_group_id": None,
            "selected_basis_candidate_ids": [],
            "selected_basis_expressions": [],
        }

    metric = "mean_validation_nrmse" if all(item["mean_validation_nrmse"] is not None for item in raw_evidence) else "mean_validation_rmse"
    variability = "std_validation_nrmse" if metric.endswith("nrmse") else "std_validation_rmse"
    for item in raw_evidence:
        item["primary_error_objective"] = metric
        item["objectives"] = {
            metric: item[metric],
            variability: item[variability],
            "symbolic_complexity": item["symbolic_complexity"],
        }
        item["objective_evidence_sha256"] = _digest(item)

    def dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        a, b = left["objectives"], right["objectives"]
        keys = (metric, variability, "symbolic_complexity")
        return all(a[key] <= b[key] for key in keys) and any(a[key] < b[key] for key in keys)

    pareto = [
        item for item in raw_evidence
        if not any(other["candidate_group_id"] != item["candidate_group_id"] and dominates(other, item) for other in raw_evidence)
    ]
    pareto.sort(key=lambda item: (
        item["objectives"][metric],
        item["objectives"]["symbolic_complexity"],
        item["objectives"][variability],
        item["candidate_group_id"],
    ))
    selected = pareto[0]
    return {
        "schema": "v60_native_multi_basis_objective_selection_v1",
        "selection_status": "selected",
        "selection_method": "verified_joint_basis_training_evidence_pareto_then_deterministic_tiebreak",
        "primary_error_objective": metric,
        "objective_directions": {metric: "minimize", variability: "minimize", "symbolic_complexity": "minimize"},
        "selection_performed": True,
        "far_or_evaluation_data_used": False,
        "input_group_count": input_count,
        "objective_group_count": len(raw_evidence),
        "rejected_group_count": len(rejected),
        "budget_truncated_count": input_count - cap,
        "objective_evidence": raw_evidence,
        "rejected_candidate_groups": rejected,
        "pareto_candidate_group_ids": [item["candidate_group_id"] for item in pareto],
        "selected_candidate_group_id": selected["candidate_group_id"],
        "selected_basis_candidate_ids": selected["basis_candidate_ids"],
        "selected_basis_expressions": selected["basis_expressions"],
        "selected_objective_evidence_sha256": selected["objective_evidence_sha256"],
    }


__all__ = ["select_native_multi_basis_candidates_from_verified_evidence"]
