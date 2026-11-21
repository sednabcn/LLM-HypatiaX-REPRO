"""Versioned discovery-report envelopes for worker boundaries.

The envelope checksum covers the complete report payload. Far-evaluation
metrics may be attached after selection, but are rejected if they claim to
have influenced selection.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any, Mapping

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryReport

ENVELOPE_SCHEMA = "v60_discovery_report_envelope_v1"


def _json_value(value: Any, path: str = "report") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must be finite")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} mapping keys must be strings")
            _json_value(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _json_value(item, f"{path}[{index}]")
        return
    raise TypeError(f"{path} contains unsupported type {type(value).__name__}")


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _is_sha256_digest(value: Any) -> bool:
    return (
        isinstance(value, str) and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def seal_discovery_report(report: DiscoveryReport | Mapping[str, Any]) -> dict[str, Any]:
    """Create a JSON-safe, checksummed envelope from a typed report or mapping."""
    payload = report.to_dict() if isinstance(report, DiscoveryReport) else dict(report)
    _json_value(payload)
    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported discovery report schema_version")
    if payload.get("far_evaluation_used_for_selection") is not False:
        raise ValueError("discovery report must explicitly exclude far evaluation from selection")
    far = payload.get("far_evaluation", {})
    if not isinstance(far, Mapping):
        raise TypeError("far_evaluation must be a mapping")
    if far.get("used_for_selection", False) is not False:
        raise ValueError("far evaluation cannot be marked as used for selection")
    envelope = {
        "envelope_schema": ENVELOPE_SCHEMA,
        "report": payload,
    }
    envelope["integrity_sha256"] = _canonical_digest(envelope)
    return envelope



def _verify_multi_basis_selection_audit(audit: Any) -> None:
    """Reconstruct the joint-basis objective, Pareto set, and winner at the worker boundary."""
    if not isinstance(audit, Mapping):
        raise TypeError("native multi-basis selection provenance must be a mapping")
    if audit.get("schema") != "v60_native_multi_basis_objective_selection_v1":
        raise ValueError("unsupported native multi-basis selection schema")
    if audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("multi-basis selection report must exclude far/evaluation data")
    status = audit.get("selection_status")
    if status not in {"selected", "no_credible_candidate", "stage_failed"}:
        raise ValueError("unsupported multi-basis selection status")
    if audit.get("selection_performed") is not (status != "stage_failed"):
        raise ValueError("multi-basis selection completion flag is inconsistent")
    evidence, pareto = audit.get("objective_evidence"), audit.get("pareto_candidate_group_ids")
    if not isinstance(evidence, list) or not isinstance(pareto, list):
        raise TypeError("multi-basis objective evidence and Pareto IDs must be lists")

    def number(value: Any, label: str, *, nonnegative: bool = True) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{label} must be a finite numeric value")
        result = float(value)
        if nonnegative and result < 0:
            raise ValueError(f"{label} cannot be negative")
        return result

    by_id = {}
    normalized = []
    for item in evidence:
        if not isinstance(item, Mapping):
            raise TypeError("multi-basis objective records must be mappings")
        gid = item.get("candidate_group_id")
        if not isinstance(gid, str) or not gid or gid in by_id:
            raise ValueError("multi-basis objective group IDs must be unique strings")
        supplied = item.get("objective_evidence_sha256")
        unsigned = {key: value for key, value in item.items() if key != "objective_evidence_sha256"}
        if not isinstance(supplied, str) or _canonical_digest(unsigned) != supplied:
            raise ValueError("multi-basis objective evidence digest does not reproduce")
        ids, expressions = item.get("basis_candidate_ids"), item.get("basis_expressions")
        if not isinstance(ids, list) or not 2 <= len(ids) <= 3 or any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("multi-basis basis IDs must be two or three unique strings")
        expected_group_id = "v60mb_" + sha256(json.dumps(ids, separators=(",", ":")).encode("utf-8")).hexdigest()[:20]
        if gid != expected_group_id:
            raise ValueError("multi-basis group ID does not match its ordered basis IDs")
        if not isinstance(item.get("source_provenance"), list):
            raise ValueError("multi-basis producer lineage must be a list")
        if not isinstance(expressions, list) or len(expressions) != len(ids) or any(not isinstance(x, str) or not x for x in expressions):
            raise ValueError("multi-basis expressions must align with basis IDs")
        fingerprint = item.get("evidence_fingerprint")
        snapshot = item.get("verified_evidence_snapshot")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64 or not isinstance(snapshot, Mapping):
            raise ValueError("multi-basis verified evidence snapshot or fingerprint is missing")
        folds, aggregates = snapshot.get("folds"), snapshot.get("aggregates")
        training_rows, variable_names, split_strategy = snapshot.get("training_row_count"), snapshot.get("variable_names"), snapshot.get("split_strategy")
        if not isinstance(folds, list) or len(folds) != item.get("fold_count") or len(folds) < 2:
            raise ValueError("embedded verified fold evidence is incomplete")
        if isinstance(training_rows, bool) or not isinstance(training_rows, int) or training_rows < 1:
            raise ValueError("embedded training row count is invalid")
        if not isinstance(variable_names, list) or not variable_names or any(not isinstance(v, str) or not v for v in variable_names):
            raise ValueError("embedded variable names are invalid")
        if not isinstance(split_strategy, str) or not split_strategy or not isinstance(aggregates, Mapping):
            raise ValueError("embedded evidence context or aggregates are invalid")
        aggregate_keys = {"validation_rmse_mean", "validation_rmse_std", "validation_nrmse_mean", "validation_nrmse_std"}
        if set(aggregates) != aggregate_keys:
            raise ValueError("embedded verified aggregate fields are incomplete")
        for key in ("validation_rmse_mean", "validation_rmse_std"):
            number(aggregates[key], key)
        for key in ("validation_nrmse_mean", "validation_nrmse_std"):
            if aggregates[key] is not None:
                number(aggregates[key], key)
        if (aggregates["validation_nrmse_mean"] is None) != (aggregates["validation_nrmse_std"] is None):
            raise ValueError("embedded normalized aggregate nullability is inconsistent")
        for index, fold in enumerate(folds):
            if not isinstance(fold, Mapping) or fold.get("fold") != index:
                raise ValueError("embedded verified folds must be ordered and complete")
            for key in ("training_row_indices", "validation_row_indices"):
                rows = fold.get(key)
                if not isinstance(rows, list) or not rows or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 or v >= training_rows for v in rows):
                    raise ValueError("embedded fold row indices are invalid")
                if len(rows) != len(set(rows)):
                    raise ValueError("embedded fold row indices must be unique")
            if set(fold["training_row_indices"]).intersection(fold["validation_row_indices"]):
                raise ValueError("embedded fold training and validation rows overlap")
            number(fold.get("recomputed_rmse"), "recomputed fold RMSE")
            for key in ("recomputed_nrmse", "recomputed_r2", "recomputed_condition_number"):
                if fold.get(key) is not None:
                    number(fold[key], key, nonnegative=(key != "recomputed_r2"))
            coeffs = fold.get("recomputed_coefficients")
            if not isinstance(coeffs, list) or len(coeffs) != len(ids) + 1:
                raise ValueError("embedded fold coefficient vector is invalid")
            for coeff in coeffs:
                number(coeff, "recomputed coefficient", nonnegative=False)
        validation_rows = [row for fold in folds for row in fold["validation_row_indices"]]
        if len(validation_rows) != len(set(validation_rows)):
            raise ValueError("embedded validation rows must be disjoint across folds")
        rmse_values = [float(fold["recomputed_rmse"]) for fold in folds]
        rmse_mean = math.fsum(rmse_values) / len(rmse_values)
        rmse_std = math.sqrt(math.fsum((value - rmse_mean) ** 2 for value in rmse_values) / len(rmse_values))
        if not math.isclose(aggregates["validation_rmse_mean"], rmse_mean, rel_tol=1e-10, abs_tol=1e-12) or not math.isclose(aggregates["validation_rmse_std"], rmse_std, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("embedded RMSE aggregates do not reproduce from verified folds")
        nrmse_values = [fold.get("recomputed_nrmse") for fold in folds]
        if all(value is not None for value in nrmse_values):
            numeric_nrmse = [float(value) for value in nrmse_values]
            nrmse_mean = math.fsum(numeric_nrmse) / len(numeric_nrmse)
            nrmse_std = math.sqrt(math.fsum((value - nrmse_mean) ** 2 for value in numeric_nrmse) / len(numeric_nrmse))
            if not math.isclose(aggregates["validation_nrmse_mean"], nrmse_mean, rel_tol=1e-10, abs_tol=1e-12) or not math.isclose(aggregates["validation_nrmse_std"], nrmse_std, rel_tol=1e-10, abs_tol=1e-12):
                raise ValueError("embedded NRMSE aggregates do not reproduce from verified folds")
        elif aggregates["validation_nrmse_mean"] is not None or aggregates["validation_nrmse_std"] is not None:
            raise ValueError("embedded NRMSE aggregate nullability does not reproduce from folds")
        fingerprint_payload = {
            "candidate_group_id": gid, "basis_candidate_ids": ids,
            "basis_expressions": expressions, "source_provenance": item.get("source_provenance"),
            "folds": folds, "aggregates": dict(aggregates),
            "training_row_count": training_rows, "variable_names": variable_names,
            "split_strategy": split_strategy,
        }
        if _canonical_digest(fingerprint_payload) != fingerprint:
            raise ValueError("embedded independent fold-evidence fingerprint does not reproduce")
        # Recompute symbolic complexity from the restricted expression parser.
        import sympy as sp
        from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression
        complexity = int(sum(sp.count_ops(parse_sympy_expression(expr, variable_names)) for expr in expressions) + len(expressions))
        if item.get("symbolic_complexity") != complexity:
            raise ValueError("multi-basis symbolic complexity does not reproduce from expressions")
        if item.get("mean_validation_rmse") != aggregates["validation_rmse_mean"] or item.get("std_validation_rmse") != aggregates["validation_rmse_std"]:
            raise ValueError("multi-basis RMSE objectives differ from verified fold aggregates")
        if item.get("mean_validation_nrmse") != aggregates["validation_nrmse_mean"] or item.get("std_validation_nrmse") != aggregates["validation_nrmse_std"]:
            raise ValueError("multi-basis NRMSE objectives differ from verified fold aggregates")
        by_id[gid] = item
        normalized.append(item)

    if status == "stage_failed":
        if evidence or pareto or audit.get("selected_candidate_group_id") is not None or audit.get("selected_basis_candidate_ids") not in ([], None) or audit.get("selected_basis_expressions") not in ([], None):
            raise ValueError("failed multi-basis selection cannot contain objective or selection evidence")
        return
    if status == "no_credible_candidate":
        if evidence or pareto or audit.get("selected_candidate_group_id") is not None or audit.get("selected_basis_candidate_ids") not in ([], None) or audit.get("selected_basis_expressions") not in ([], None):
            raise ValueError("no-credible-candidate decision must have empty selection evidence")
        return
    if not normalized:
        raise ValueError("selected multi-basis decision requires objective evidence")

    metric = "mean_validation_nrmse" if all(x.get("mean_validation_nrmse") is not None for x in normalized) else "mean_validation_rmse"
    variability = "std_validation_nrmse" if metric.endswith("nrmse") else "std_validation_rmse"
    if audit.get("primary_error_objective") != metric:
        raise ValueError("multi-basis primary error objective does not match the complete evidence pool")
    directions = {metric: "minimize", variability: "minimize", "symbolic_complexity": "minimize"}
    if audit.get("objective_directions") != directions:
        raise ValueError("multi-basis objective directions are inconsistent")
    for item in normalized:
        expected = {metric: number(item[metric], metric), variability: number(item[variability], variability), "symbolic_complexity": number(item["symbolic_complexity"], "symbolic_complexity")}
        if item.get("primary_error_objective") != metric or item.get("objectives") != expected:
            raise ValueError("multi-basis objective vector does not reproduce from verified metrics")

    def dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        a, b = left["objectives"], right["objectives"]
        keys = (metric, variability, "symbolic_complexity")
        return all(a[k] <= b[k] for k in keys) and any(a[k] < b[k] for k in keys)

    frontier = [item for item in normalized if not any(other["candidate_group_id"] != item["candidate_group_id"] and dominates(other, item) for other in normalized)]
    frontier.sort(key=lambda item: (item["objectives"][metric], item["objectives"]["symbolic_complexity"], item["objectives"][variability], item["candidate_group_id"]))
    expected_ids = [item["candidate_group_id"] for item in frontier]
    if pareto != expected_ids:
        raise ValueError("serialized Pareto membership/order does not reproduce from objective evidence")
    winner = frontier[0]
    selected_id = audit.get("selected_candidate_group_id")
    if selected_id != winner["candidate_group_id"]:
        raise ValueError("selected multi-basis group does not match deterministic Pareto tie-break")
    if audit.get("selected_basis_candidate_ids") != winner["basis_candidate_ids"] or audit.get("selected_basis_expressions") != winner["basis_expressions"]:
        raise ValueError("selected multi-basis basis references do not match the deterministic winner")
    if audit.get("selected_objective_evidence_sha256") != winner["objective_evidence_sha256"]:
        raise ValueError("selected multi-basis objective digest does not match")

def _verify_native_final_model_audit(audit: Any) -> None:
    """Verify the final-model identity and ensure far evidence is post-selection only."""
    if not isinstance(audit, Mapping):
        raise TypeError("native final-model provenance must be a mapping")
    if audit.get("schema") != "v60_native_final_model_v1":
        raise ValueError("unsupported native final-model schema")
    if audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("native final model must certify training-only selection")
    status = audit.get("execution_status")
    if status == "selected":
        if audit.get("selection_performed") is not True:
            raise ValueError("selected native final model must mark selection_performed=true")
        model = audit.get("selected_model")
        supplied = audit.get("selected_model_sha256")
        if not isinstance(model, Mapping) or not _is_sha256_digest(supplied):
            raise ValueError("selected native final model is missing its identity digest")
        canonical = json.dumps(dict(model), sort_keys=True, separators=(",", ":"), allow_nan=False)
        if sha256(canonical.encode("utf-8")).hexdigest() != supplied:
            raise ValueError("native final-model digest verification failed")
        expressions = model.get("basis_expressions")
        ids = model.get("basis_candidate_ids")
        coefficients = model.get("coefficients")
        names = model.get("variable_names")
        if (not isinstance(expressions, list) or not 1 <= len(expressions) <= 3
                or not isinstance(ids, list) or len(ids) != len(expressions)
                or not isinstance(coefficients, list) or len(coefficients) != len(expressions) + 1):
            raise ValueError("native final-model basis/coefficients dimensions are inconsistent")
        if (any(not isinstance(value, str) or not value for value in ids)
                or len(ids) != len(set(ids))):
            raise ValueError("native final-model basis IDs must be unique non-empty strings")
        family = model.get("family")
        candidate_id = model.get("candidate_id")
        group_id = model.get("candidate_group_id")
        if family == "single_basis":
            if (len(expressions) != 1 or not isinstance(candidate_id, str)
                    or not candidate_id or group_id is not None or ids != [candidate_id]):
                raise ValueError("single-basis final model identity is inconsistent")
        elif family == "multi_basis":
            if (not 2 <= len(expressions) <= 3 or candidate_id is not None
                    or not isinstance(group_id, str) or not group_id):
                raise ValueError("multi-basis final model identity is inconsistent")
        else:
            raise ValueError("selected model family is unsupported")
        if (not isinstance(names, list) or not names
                or any(not isinstance(value, str) or not value for value in names)
                or len(names) != len(set(names))):
            raise ValueError("native final-model variable names must be unique non-empty strings")
        numeric_coefficients = []
        for value in coefficients:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError("native final-model coefficients must be finite numbers")
            numeric_coefficients.append(float(value))
        if any(not isinstance(value, str) or not value for value in expressions):
            raise ValueError("native final-model expressions must be non-empty strings")
        # The digest only detects accidental mutation: it is not a signature.
        # Re-parse every basis and reconstruct the outward formula so a worker
        # also rejects a self-consistently re-hashed but semantically altered model.
        from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression
        for expression in expressions:
            parse_sympy_expression(expression, names)
        expected_formula = " + ".join(
            [f"({coefficient:.17g})*({expression})"
             for coefficient, expression in zip(numeric_coefficients[:-1], expressions)]
            + [f"({numeric_coefficients[-1]:.17g})"]
        )
        if model.get("fitted_expression") != expected_formula:
            raise ValueError("native final-model fitted expression does not reproduce from its bases and coefficients")
        # Reconstruct the cross-family winner from the serialized, training-only
        # objective options. A recomputed model digest must not let a producer
        # substitute a different single-/multi-basis winner.
        options = audit.get("candidate_options")
        if not isinstance(options, list) or not 1 <= len(options) <= 2:
            raise ValueError("native final-model candidate_options must contain one or two family winners")
        families = []
        checked_options = []
        for option in options:
            if not isinstance(option, Mapping):
                raise ValueError("native final-model candidate option must be a mapping")
            family = option.get("family")
            if family not in {"single_basis", "multi_basis"} or family in families:
                raise ValueError("native final-model candidate families must be unique and recognized")
            families.append(family)
            for key in ("cv_rmse", "cv_rmse_std"):
                value = option.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
                    raise ValueError(f"native final-model option {key} must be finite and non-negative")
            for key in ("cv_nrmse", "cv_nrmse_std"):
                value = option.get(key)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0):
                    raise ValueError(f"native final-model option {key} must be finite, non-negative, or null")
            if (option.get("cv_nrmse") is None) != (option.get("cv_nrmse_std") is None):
                raise ValueError("native final-model option NRMSE mean/std nullability must match")
            complexity = option.get("complexity")
            if isinstance(complexity, bool) or not isinstance(complexity, int) or complexity < 0:
                raise ValueError("native final-model option complexity must be a non-negative integer")
            expressions_option = option.get("expressions")
            if not isinstance(expressions_option, list) or not 1 <= len(expressions_option) <= 3:
                raise ValueError("native final-model option expressions are invalid")
            if any(not isinstance(value, str) or not value for value in expressions_option):
                raise ValueError("native final-model option expressions must be non-empty strings")
            for expression in expressions_option:
                parse_sympy_expression(expression, names)
            if family == "single_basis":
                if (len(expressions_option) != 1 or not isinstance(option.get("candidate_id"), str)
                        or not option.get("candidate_id") or option.get("candidate_group_id") is not None):
                    raise ValueError("single-basis final-model option has invalid identity")
            else:
                ids_option = option.get("candidate_ids")
                if (not isinstance(ids_option, list) or len(ids_option) != len(expressions_option)
                        or not 2 <= len(ids_option) <= 3
                        or any(not isinstance(value, str) or not value for value in ids_option)
                        or len(ids_option) != len(set(ids_option))
                        or option.get("candidate_id") is not None
                        or not isinstance(option.get("candidate_group_id"), str)
                        or not option.get("candidate_group_id")):
                    raise ValueError("multi-basis final-model option has invalid basis lineage")
            checked_options.append(option)
        use_nrmse = all(option.get("cv_nrmse") is not None for option in checked_options)
        expected_metric = "cv_nrmse" if use_nrmse else "cv_rmse"
        expected_variability = "cv_nrmse_std" if use_nrmse else "cv_rmse_std"
        expected_winner = min(checked_options, key=lambda option: (
            float(option[expected_metric]),
            float(option[expected_variability]) if option.get(expected_variability) is not None else float("inf"),
            int(option["complexity"]), option["family"],
        ))
        expected_ids = (
            [expected_winner["candidate_id"]]
            if expected_winner["family"] == "single_basis"
            else list(expected_winner["candidate_ids"])
        )
        expected_candidate_id = expected_winner.get("candidate_id") if expected_winner["family"] == "single_basis" else None
        expected_group_id = expected_winner.get("candidate_group_id") if expected_winner["family"] == "multi_basis" else None
        if (audit.get("objective_metric") != expected_metric
                or model.get("selection_metric") != expected_metric
                or model.get("family") != expected_winner["family"]
                or model.get("candidate_id") != expected_candidate_id
                or model.get("candidate_group_id") != expected_group_id
                or model.get("basis_candidate_ids") != expected_ids
                or model.get("basis_expressions") != expected_winner["expressions"]
                or model.get("cross_validation_metric") != expected_winner[expected_metric]
                or model.get("cross_validation_metric_std") != expected_winner.get(expected_variability)
                or model.get("symbolic_complexity") != expected_winner["complexity"]):
            raise ValueError("native final model does not match the reconstructed cross-family selection winner")
        row_count = model.get("training_row_count")
        if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 1:
            raise ValueError("native final-model training row count must be a positive integer")
        for key in ("training_target_std", "training_rmse"):
            value = model.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f"native final-model {key} must be finite and non-negative")
        for key in ("training_nrmse", "training_r2", "training_design_condition_number"):
            value = model.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))):
                raise ValueError(f"native final-model {key} must be finite or null")
        training_nrmse = model.get("training_nrmse")
        target_std = float(model["training_target_std"])
        training_rmse = float(model["training_rmse"])
        if training_nrmse is not None and float(training_nrmse) < 0:
            raise ValueError("native final-model training_nrmse must be non-negative or null")
        if target_std > 0:
            expected_nrmse = training_rmse / target_std
            if training_nrmse is None or not math.isclose(
                float(training_nrmse), expected_nrmse, rel_tol=1e-9, abs_tol=1e-12,
            ):
                raise ValueError("native final-model training NRMSE does not reproduce from RMSE and target standard deviation")
        elif training_nrmse is not None:
            raise ValueError("native final-model training NRMSE must be null for a zero-variance target")
        condition_number = model.get("training_design_condition_number")
        if condition_number is not None and float(condition_number) < 0:
            raise ValueError("native final-model design condition number cannot be negative")
        rank = model.get("training_design_rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != len(expressions) + 1:
            raise ValueError("native final-model training design must have full column rank")
    elif status in {"no_credible_candidate", "stage_failed", "not_run"}:
        if audit.get("selection_performed") is not False:
            raise ValueError("unselected native final model cannot claim selection")
        if audit.get("selected_model") is not None:
            raise ValueError("unselected native final model cannot carry a selected model")
    else:
        raise ValueError("unsupported native final-model execution status")


def _verify_native_far_evaluation_audit(
    audit: Any, final_model_audit: Any = None,
) -> None:
    """Verify the frozen evaluation contract and bind it to the selected model."""
    if not isinstance(audit, Mapping):
        raise TypeError("far_evaluation must be a mapping")
    if audit.get("used_for_selection", False) is not False:
        raise ValueError("far evaluation cannot be used for selection")
    if audit.get("far_or_evaluation_data_used_for_selection", False) is not False:
        raise ValueError("far evaluation contamination flag must be false")
    if audit.get("far_or_evaluation_data_used_for_retry", False) is not False:
        raise ValueError("far evaluation cannot influence retries")
    if audit.get("candidate_ranking_performed", False) is not False:
        raise ValueError("far evaluation cannot rank candidates")
    if audit.get("selection_changed", False) is not False:
        raise ValueError("frozen far evaluation cannot change selection")
    if audit.get("selection_performed", False) is not False:
        raise ValueError("far evaluation stage cannot perform selection")
    status = audit.get("evaluation_status")
    if status is None:
        if audit:
            raise ValueError("non-empty far evaluation audit requires an evaluation_status")
        return
    if status not in {"completed", "stage_failed", "blocked_no_selected_model"}:
        raise ValueError("unsupported frozen far-evaluation status")
    if audit.get("schema") != "v60_native_frozen_model_evaluation_v1":
        raise ValueError("unsupported frozen far-evaluation schema")
    if status == "completed":
        digest = audit.get("selected_model_sha256")
        far_digest = audit.get("far_set_sha256")
        if not _is_sha256_digest(digest) or not _is_sha256_digest(far_digest):
            raise ValueError("completed far evaluation requires valid lowercase SHA-256 model and far-set digests")
        if (not isinstance(final_model_audit, Mapping)
                or final_model_audit.get("execution_status") != "selected"
                or final_model_audit.get("selection_performed") is not True):
            raise ValueError("completed far evaluation requires the selected final-model audit")
        if digest != final_model_audit.get("selected_model_sha256"):
            raise ValueError("far evaluation model digest does not match the finalized native model")
        if audit.get("evaluation_scope") != "single_frozen_finalized_model":
            raise ValueError("far evaluation must describe exactly one frozen finalized model")
        row_count = audit.get("far_row_count")
        if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 1:
            raise ValueError("completed far evaluation requires a positive integer far_row_count")
        metrics = audit.get("far_metrics")
        if not isinstance(metrics, Mapping) or set(metrics) != {
            "rmse", "nrmse_by_training_target_std", "mae", "bias", "r2",
        }:
            raise ValueError("completed far evaluation metrics have an invalid schema")
        for key in ("rmse", "mae"):
            value = metrics.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f"far evaluation {key} must be finite and non-negative")
        for key in ("nrmse_by_training_target_std", "r2"):
            value = metrics.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))):
                raise ValueError(f"far evaluation {key} must be finite or null")
        normalized_rmse = metrics.get("nrmse_by_training_target_std")
        if normalized_rmse is not None and float(normalized_rmse) < 0:
            raise ValueError("far evaluation nrmse_by_training_target_std must be non-negative or null")
        bias = metrics.get("bias")
        if isinstance(bias, bool) or not isinstance(bias, (int, float)) or not math.isfinite(float(bias)):
            raise ValueError("far evaluation bias must be finite")
    elif audit.get("far_metrics") is not None:
        raise ValueError("incomplete far evaluation cannot publish far metrics")


def _verify_native_residual_diagnostics(audit: Any) -> None:
    """Ensure residual diagnostics remain descriptive, training-only evidence."""
    if not isinstance(audit, Mapping):
        raise TypeError("native residual diagnostics must be a mapping")
    if audit.get("schema") != "v60_native_residual_stability_v1":
        raise ValueError("unsupported native residual diagnostics schema")
    if audit.get("selection_performed") is not False:
        raise ValueError("residual diagnostics cannot perform selection")
    if audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("residual diagnostics must be training-only")


def verify_discovery_report_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Strictly verify worker input; return a detached JSON-compatible report."""
    if not isinstance(envelope, Mapping):
        raise TypeError("discovery report envelope must be a mapping")
    if set(envelope) != {"envelope_schema", "report", "integrity_sha256"}:
        raise ValueError("discovery report envelope has missing or unknown fields")
    if envelope.get("envelope_schema") != ENVELOPE_SCHEMA:
        raise ValueError("unsupported discovery report envelope schema")
    supplied = envelope.get("integrity_sha256")
    if not _is_sha256_digest(supplied):
        raise ValueError("invalid discovery report integrity digest")
    unsigned = {"envelope_schema": envelope["envelope_schema"], "report": envelope["report"]}
    _json_value(unsigned)
    if _canonical_digest(unsigned) != supplied:
        raise ValueError("discovery report integrity verification failed")
    report = envelope["report"]
    if not isinstance(report, Mapping):
        raise TypeError("discovery report payload must be a mapping")
    required = {
        "schema_version", "status", "selected_candidate_id", "pareto_candidate_ids",
        "candidates", "failure_reasons", "provenance", "far_evaluation",
        "far_evaluation_used_for_selection",
    }
    if set(report) != required:
        raise ValueError("discovery report payload has missing or unknown fields")
    if report["schema_version"] != "1.0":
        raise ValueError("unsupported discovery report schema_version")
    if report["far_evaluation_used_for_selection"] is not False:
        raise ValueError("far evaluation contamination flag must be false")
    if not isinstance(report["far_evaluation"], Mapping):
        raise TypeError("far_evaluation must be a mapping")
    if report["far_evaluation"].get("used_for_selection", False) is not False:
        raise ValueError("far evaluation cannot influence selection")
    provenance = report["provenance"]
    if not isinstance(provenance, Mapping):
        raise TypeError("report provenance must be a mapping")
    if "native_multi_basis_selection" in provenance:
        _verify_multi_basis_selection_audit(provenance["native_multi_basis_selection"])
    final_model_audit = provenance.get("native_final_model")
    if "native_final_model" in provenance:
        _verify_native_final_model_audit(final_model_audit)
    if "native_split_conformal_calibration" in provenance:
        if not isinstance(final_model_audit, Mapping):
            raise ValueError("split-conformal calibration requires an embedded finalized native model")
        from hypatiax.tools.symbolic.v60_production_handoff import verify_native_v60_calibration_audit
        verify_native_v60_calibration_audit(
            final_model_audit, provenance["native_split_conformal_calibration"]
        )
    if "native_residual_diagnostics" in provenance:
        _verify_native_residual_diagnostics(provenance["native_residual_diagnostics"])
    _verify_native_far_evaluation_audit(report["far_evaluation"], final_model_audit)
    candidates = report["candidates"]
    if not isinstance(candidates, list):
        raise TypeError("candidates must be a list")
    candidate_ids = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or not isinstance(candidate.get("candidate_id"), str):
            raise TypeError("each candidate must contain a string candidate_id")
        candidate_ids.append(candidate["candidate_id"])
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate IDs must be unique")
    selected = report["selected_candidate_id"]
    if selected is not None and selected not in candidate_ids:
        raise ValueError("selected candidate must exist in report candidates")
    pareto = report["pareto_candidate_ids"]
    if not isinstance(pareto, list) or not set(pareto).issubset(set(candidate_ids)):
        raise ValueError("Pareto IDs must reference report candidates")
    return json.loads(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def attach_native_v60_calibration_to_report(
    envelope: Mapping[str, Any], calibration_audit: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach a verified post-selection calibration audit to a sealed report."""
    report = verify_discovery_report_envelope(envelope)
    provenance = dict(report["provenance"])
    final_model_audit = provenance.get("native_final_model")
    if not isinstance(final_model_audit, Mapping):
        raise ValueError("discovery report does not contain a finalized native V60 model")
    from hypatiax.tools.symbolic.v60_production_handoff import verify_native_v60_calibration_audit
    provenance["native_split_conformal_calibration"] = verify_native_v60_calibration_audit(
        final_model_audit, calibration_audit
    )
    report["provenance"] = provenance
    return seal_discovery_report(report)


__all__ = ["ENVELOPE_SCHEMA", "seal_discovery_report", "verify_discovery_report_envelope", "build_native_discovery_report", "attach_native_v60_calibration_to_report"]


def build_native_discovery_report(
    proposals: list[Mapping[str, Any]],
    gate_audit: Mapping[str, Any],
    validation_audit: Mapping[str, Any],
    selection_audit: Mapping[str, Any],
    *,
    run_context: Mapping[str, Any],
    multi_basis_selection_audit: Mapping[str, Any] | None = None,
    final_model_audit: Mapping[str, Any] | None = None,
    far_evaluation_audit: Mapping[str, Any] | None = None,
    residual_stability_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a versioned report from native V60 evidence without promoting it
    to the V50.2 production result.
    """
    from hypatiax.tools.symbolic.discovery_contracts import CandidateRecord, DiscoveryReport

    gate_by_id = {
        item.get("native_candidate_id"): item
        for item in gate_audit.get("candidate_gates", [])
        if isinstance(item, Mapping)
    }
    validation_by_id = {
        item.get("candidate_id"): item
        for item in validation_audit.get("candidate_validation", [])
        if isinstance(item, Mapping)
    }
    objective_by_id = {
        item.get("candidate_id"): item
        for item in selection_audit.get("objective_evidence", [])
        if isinstance(item, Mapping)
    }
    records = []
    native_to_report = {}
    for proposal in proposals:
        native_id = proposal.get("candidate_id")
        lineage = proposal.get("producer_provenance") or [{}]
        producer = lineage[0] if isinstance(lineage, list) else {}
        source = producer.get("source", "unknown")
        if source not in {"llm_proposal", "domain_template", "pysr_search", "residual_search", "unknown"}:
            source = "unknown"
        strategy = producer.get("search_strategy", "native_template")
        seed = producer.get("seed", 0)
        if not isinstance(seed, int) or isinstance(seed, bool):
            seed = 0
        gate = gate_by_id.get(native_id, {})
        validation = validation_by_id.get(native_id, {})
        objective = objective_by_id.get(native_id, {})
        metrics = {}
        if isinstance(validation, Mapping):
            metrics["training_validation"] = dict(validation)
        if isinstance(objective, Mapping):
            metrics["training_objectives"] = dict(objective)
        record = CandidateRecord(
            expression=str(proposal.get("expression") or proposal.get("normalized_expression") or ""),
            normalized_expression=str(proposal.get("normalized_expression") or proposal.get("expression") or ""),
            source=source,
            search_strategy=str(strategy),
            seed=seed,
            metrics=metrics,
            rejection_reasons=tuple(gate.get("rejection_reasons", ())) if isinstance(gate, Mapping) else (),
            eligible=bool(gate.get("eligible", False)) if isinstance(gate, Mapping) else False,
        )
        records.append(record)
        native_to_report[native_id] = record.candidate_id

    selected_native = selection_audit.get("selected_candidate_id")
    selected_report = native_to_report.get(selected_native)
    pareto_report = [
        native_to_report[item]
        for item in selection_audit.get("pareto_candidate_ids", [])
        if item in native_to_report
    ]
    selected = selection_audit.get("selection_status") == "selected" and selected_report is not None
    status = "provisional" if selected else "no_credible_candidate"
    failures = []
    if not selected:
        reason = selection_audit.get("reason") or selection_audit.get("selection_status") or "native selection produced no candidate"
        failures.append(str(reason))
    report = DiscoveryReport(
        status=status,
        candidates=tuple(records),
        selected_candidate_id=selected_report if selected else None,
        pareto_candidate_ids=tuple(pareto_report),
        failure_reasons=tuple(failures),
        provenance={
            "engine_version": "6.0.0",
            "implementation_mode": "native_v60_audit_with_v50_2_compatibility",
            "native_v60_pipeline": False,
            "run_context": dict(run_context),
            "native_selection_status": selection_audit.get("selection_status"),
            "native_multi_basis_selection": dict(multi_basis_selection_audit or {
                "schema": "v60_native_multi_basis_objective_selection_v1",
                "selection_status": "stage_failed", "selection_performed": False,
                "far_or_evaluation_data_used": False, "objective_evidence": [],
                "pareto_candidate_group_ids": [], "selected_candidate_group_id": None,
                "selected_basis_candidate_ids": [], "selected_basis_expressions": [],
            }),
            "native_residual_diagnostics": dict(residual_stability_audit or {
                "schema": "v60_native_residual_stability_v1", "diagnostic_status": "not_run",
                "selection_performed": False, "far_or_evaluation_data_used": False,
            }),
            "native_final_model": dict(final_model_audit or {
                "schema": "v60_native_final_model_v1", "execution_status": "not_run",
                "selection_performed": False, "far_or_evaluation_data_used": False,
                "selected_model": None,
            }),
            "compatibility_baseline": "hybrid_system_v50_2",
        },
        far_evaluation={**dict(far_evaluation_audit or {}), "used_for_selection": False},
    )
    return seal_discovery_report(report)


__all__ = ["ENVELOPE_SCHEMA", "seal_discovery_report", "verify_discovery_report_envelope", "build_native_discovery_report", "attach_native_v60_calibration_to_report"]
