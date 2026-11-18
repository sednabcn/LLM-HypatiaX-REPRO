#!/usr/bin/env python3
"""Validate one REPRO worker's Exp2 Feynman extrapolation outputs.

This is an offline structural/provenance gate. It does not run experiments,
load model backends, or call any LLM API.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_METHOD_COUNT = 6
REQUIRED_DISCOVERY_REPORT_METHOD = "HybridDiscoverySystem v50_2 (tools)"


def _reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-standard JSON numeric token: {token}")


def _load_strict_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



DISCOVERY_REPORT_SCHEMA_VERSIONS = {"1.0", "discovery_contract_v1"}
DISCOVERY_REPORT_STATUSES = {
    "accepted", "provisional", "no_credible_candidate",
    "invalid_problem_specification", "no_candidates_generated",
    "all_candidates_failed_symbolic_validation",
    "all_candidates_failed_physical_gates", "insufficient_validation_evidence",
    "search_budget_exhausted", "llm_unavailable_fallback_used",
    "accepted_with_warnings",
}
DISCOVERY_CANDIDATE_SOURCES = {
    "llm_proposal", "domain_template", "pysr_search", "residual_search", "unknown",
}
DISCOVERY_CONSTRAINT_STATUSES = {
    "pass", "fail", "warning", "not_applicable", "unknown", "not_checked",
}



def _validate_soft_constraint_pareto_contract(report: dict[str, Any]) -> None:
    """Validate serialized soft-constraint Pareto provenance and candidate audit."""
    provenance = report.get("provenance", {})
    if not isinstance(provenance, dict):
        return
    policy = provenance.get("selection_policy")
    supported = {
        "training_only_pareto_v5_soft_constraints",
        "training_only_pareto_v6_nested_structure_soft_constraints",
    }
    if policy not in supported:
        return
    constraint_ids = provenance.get("soft_constraint_ids")
    if (not isinstance(constraint_ids, list) or not constraint_ids
        or any(not isinstance(item, str) or not item for item in constraint_ids)
        or len(constraint_ids) != len(set(constraint_ids))):
        raise ValueError("soft-constraint Pareto policy requires unique declared soft_constraint_ids")
    if provenance.get("soft_constraint_aggregation") != "unweighted_mean_of_declared_violation_fractions":
        raise ValueError("soft-constraint Pareto policy has unsupported aggregation")
    if "mean_declared_soft_constraint_violation_fraction_min" not in provenance.get("objectives", []):
        raise ValueError("soft-constraint Pareto policy is missing its declared objective")
    for index, candidate in enumerate(report["candidates"]):
        metrics = candidate.get("metrics", {})
        selection = metrics.get("pareto_selection") if isinstance(metrics, dict) else None
        if not isinstance(selection, dict):
            raise ValueError(f"soft-constraint candidate[{index}] is missing Pareto selection audit")
        if selection.get("declared_soft_constraint_ids") != constraint_ids:
            raise ValueError(f"soft-constraint candidate[{index}] declared IDs differ from report provenance")
        matching = [
            item for item in candidate["constraint_outcomes"]
            if item["constraint_id"] in set(constraint_ids)
        ]
        complete = len(matching) == len(constraint_ids) and {item["constraint_id"] for item in matching} == set(constraint_ids)
        fractions: list[float] = []
        if complete:
            by_id = {item["constraint_id"]: item for item in matching}
            for constraint_id in constraint_ids:
                outcome = by_id[constraint_id]
                evidence = outcome["evidence"]
                count, violations, fraction = evidence.get("evaluation_count"), evidence.get("violation_count"), evidence.get("violation_fraction")
                if (outcome["severity"] != "soft" or outcome["status"] not in {"pass", "fail"}
                    or isinstance(count, bool) or not isinstance(count, int) or count <= 0
                    or isinstance(violations, bool) or not isinstance(violations, int)
                    or not 0 <= violations <= count or isinstance(fraction, bool)
                    or not isinstance(fraction, (int, float)) or not math.isfinite(float(fraction))
                    or not 0.0 <= float(fraction) <= 1.0
                    or not math.isclose(float(fraction), violations / count, rel_tol=1e-9, abs_tol=1e-12)
                    or ((outcome["status"] == "pass") != (violations == 0))):
                    complete = False
                    break
                fractions.append(float(fraction))
        aggregate = sum(fractions) / len(fractions) if complete else None
        recorded = selection.get("mean_soft_constraint_violation_fraction")
        if aggregate is None:
            if "soft_constraint_evidence_incomplete" not in selection.get("eligibility_reasons", []):
                raise ValueError(f"soft-constraint candidate[{index}] incomplete evidence lacks exclusion reason")
            if recorded is not None:
                raise ValueError(f"soft-constraint candidate[{index}] records an aggregate without complete evidence")
            if selection.get("eligible_for_pareto") is True:
                raise ValueError(f"soft-constraint candidate[{index}] with incomplete evidence is Pareto-eligible")
        else:
            if isinstance(recorded, bool) or not isinstance(recorded, (int, float)) or not math.isclose(float(recorded), aggregate, rel_tol=1e-9, abs_tol=1e-12):
                raise ValueError(f"soft-constraint candidate[{index}] aggregate does not match declared outcomes")
            objectives = selection.get("objectives")
            if selection.get("eligible_for_pareto") is True and (
                not isinstance(objectives, dict)
                or not math.isclose(float(objectives.get("mean_soft_constraint_violation_fraction", float("nan"))), aggregate, rel_tol=1e-9, abs_tol=1e-12)
            ):
                raise ValueError(f"soft-constraint candidate[{index}] Pareto objective differs from audited aggregate")


def _validate_pareto_selection_consistency(report: dict[str, Any]) -> None:
    """Recompute the serialized Pareto front and deterministic winner."""
    provenance = report.get("provenance", {})
    if not isinstance(provenance, dict):
        return
    policy = provenance.get("selection_policy")
    policy_objectives = {
        "training_only_pareto_v3_stability": (
            "mean_normalized_rmse", "worst_normalized_rmse", "complexity",
            "negative_expression_stability",
        ),
        "training_only_pareto_v4_nested_structure_stability": (
            "mean_normalized_rmse", "worst_normalized_rmse", "complexity",
            "negative_expression_stability",
        ),
        "training_only_pareto_v5_soft_constraints": (
            "mean_normalized_rmse", "worst_normalized_rmse", "complexity",
            "negative_expression_stability", "mean_soft_constraint_violation_fraction",
        ),
        "training_only_pareto_v6_nested_structure_soft_constraints": (
            "mean_normalized_rmse", "worst_normalized_rmse", "complexity",
            "negative_expression_stability", "mean_soft_constraint_violation_fraction",
        ),
    }
    if policy not in policy_objectives:
        return
    expected_keys = policy_objectives[policy]
    objective_names = [
        "mean_normalized_rmse_min", "worst_normalized_rmse_min",
        "symbolic_operation_count_min", "expression_stability_fraction_max",
    ]
    if len(expected_keys) == 5:
        objective_names.append("mean_declared_soft_constraint_violation_fraction_min")
    recorded_names = provenance.get("objectives")
    candidates = report.get("candidates", [])
    eligible_vectors: dict[str, dict[str, float]] = {}
    for index, candidate in enumerate(candidates):
        metrics = candidate.get("metrics", {})
        selection = metrics.get("pareto_selection") if isinstance(metrics, dict) else None
        if not isinstance(selection, dict):
            raise ValueError(f"Pareto candidate[{index}] is missing selection audit")
        reasons = selection.get("eligibility_reasons")
        eligible = selection.get("eligible_for_pareto")
        if (not isinstance(reasons, list) or any(not isinstance(item, str) for item in reasons)
            or not isinstance(eligible, bool) or eligible != (len(reasons) == 0)):
            raise ValueError(f"Pareto candidate[{index}] eligibility flag/reasons are inconsistent")
        vector = selection.get("objectives")
        if eligible:
            if not isinstance(vector, dict) or set(vector) != set(expected_keys):
                raise ValueError(f"Pareto candidate[{index}] has an incomplete objective vector")
            normalized: dict[str, float] = {}
            for key in expected_keys:
                value = vector[key]
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))):
                    raise ValueError(f"Pareto candidate[{index}] objective {key!r} is not finite")
                normalized[key] = float(value)
            validation = metrics.get("training_validation", {})
            folds = validation.get("fold_metrics", []) if isinstance(validation, dict) else []
            if not isinstance(folds, list):
                raise ValueError(f"Pareto candidate[{index}] training fold metrics must be a list")
            fold_scores = []
            for fold in folds:
                if not isinstance(fold, dict):
                    continue
                score = fold.get("normalized_rmse")
                if (isinstance(score, (int, float)) and not isinstance(score, bool)
                    and math.isfinite(float(score)) and float(score) >= 0):
                    fold_scores.append(float(score))
            if selection.get("valid_normalized_fold_count") != len(fold_scores):
                raise ValueError(f"Pareto candidate[{index}] fold count audit does not match training evidence")
            if not fold_scores:
                raise ValueError(f"Pareto candidate[{index}] lacks finite training fold scores")
            expected_training_values = {
                "mean_normalized_rmse": sum(fold_scores) / len(fold_scores),
                "worst_normalized_rmse": max(fold_scores),
            }
            complexity = selection.get("complexity_node_count")
            stability = selection.get("expression_stability_fraction")
            if isinstance(complexity, bool) or not isinstance(complexity, int) or complexity < 0:
                raise ValueError(f"Pareto candidate[{index}] complexity audit is invalid")
            supplied_complexity = metrics.get("complexity")
            if isinstance(supplied_complexity, dict) and "node_count" in supplied_complexity:
                supplied_node_count = supplied_complexity.get("node_count")
                if (isinstance(supplied_node_count, bool) or not isinstance(supplied_node_count, int)
                    or supplied_node_count < 0 or supplied_node_count != complexity):
                    raise ValueError(f"Pareto candidate[{index}] complexity objective does not match supplied complexity evidence")
            else:
                expression = candidate.get("normalized_expression") or candidate.get("expression")
                parser_path = Path(__file__).resolve().parents[2] / "hypatiax" / "tools" / "validation" / "safe_sympy_parser.py"
                spec = importlib.util.spec_from_file_location(
                    "_exp2_safe_sympy_parser", parser_path
                )
                if spec is None or spec.loader is None:
                    raise ValueError(f"Pareto candidate[{index}] safe expression parser is unavailable")
                parser_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(parser_module)
                try:
                    import sympy as sp
                    parsed = parser_module.parse_sympy_expression(expression)
                    recomputed_complexity = int(sp.count_ops(parsed, visual=False))
                except Exception as exc:
                    raise ValueError(
                        f"Pareto candidate[{index}] complexity cannot be recomputed from its expression"
                    ) from exc
                if complexity != recomputed_complexity:
                    raise ValueError(
                        f"Pareto candidate[{index}] complexity objective does not match parsed expression"
                    )
            if (isinstance(stability, bool) or not isinstance(stability, (int, float))
                or not math.isfinite(float(stability)) or not 0.0 <= float(stability) <= 1.0):
                raise ValueError(f"Pareto candidate[{index}] expression stability audit is invalid")
            stability_evidence = validation.get("expression_stability")
            if not isinstance(stability_evidence, dict) or stability_evidence.get("status") != "measured":
                raise ValueError(f"Pareto candidate[{index}] lacks measured expression-stability evidence")
            evidence_fraction = stability_evidence.get("dominant_fraction")
            if (isinstance(evidence_fraction, bool) or not isinstance(evidence_fraction, (int, float))
                or not math.isfinite(float(evidence_fraction)) or not 0.0 <= float(evidence_fraction) <= 1.0
                or not math.isclose(float(stability), float(evidence_fraction), rel_tol=1e-9, abs_tol=1e-12)):
                raise ValueError(f"Pareto candidate[{index}] stability objective does not match training evidence")
            expected_training_values.update({
                "complexity": float(complexity),
                "negative_expression_stability": -float(stability),
            })
            if len(expected_keys) == 5:
                soft_value = selection.get("mean_soft_constraint_violation_fraction")
                if (isinstance(soft_value, bool) or not isinstance(soft_value, (int, float))
                    or not math.isfinite(float(soft_value)) or not 0.0 <= float(soft_value) <= 1.0):
                    raise ValueError(f"Pareto candidate[{index}] soft-constraint objective audit is invalid")
                expected_training_values["mean_soft_constraint_violation_fraction"] = float(soft_value)
            for key, expected_value in expected_training_values.items():
                if not math.isclose(normalized[key], expected_value, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError(
                        f"Pareto candidate[{index}] objective {key!r} does not match underlying training evidence"
                    )
            eligible_vectors[candidate["candidate_id"]] = normalized
        elif vector is not None:
            raise ValueError(f"Pareto-ineligible candidate[{index}] must not carry an objective vector")

    if not eligible_vectors:
        if report.get("pareto_candidate_ids") or report.get("selected_candidate_id") is not None:
            raise ValueError("empty eligible Pareto set must not declare Pareto or selected candidates")
        return
    if recorded_names != objective_names:
        raise ValueError("Pareto provenance objective names do not match the selection policy")

    ids = list(eligible_vectors)
    expected_front = [
        candidate_id for candidate_id in ids
        if not any(
            other_id != candidate_id
            and all(eligible_vectors[other_id][key] <= eligible_vectors[candidate_id][key] for key in expected_keys)
            and any(eligible_vectors[other_id][key] < eligible_vectors[candidate_id][key] for key in expected_keys)
            for other_id in ids
        )
    ]
    if report.get("pareto_candidate_ids") != expected_front:
        raise ValueError("serialized Pareto candidate IDs do not match recomputed objective front")

    def tie_break(candidate_id: str) -> tuple[Any, ...]:
        vector = eligible_vectors[candidate_id]
        return (
            vector["mean_normalized_rmse"],
            vector["worst_normalized_rmse"],
            vector["complexity"],
            vector.get("mean_soft_constraint_violation_fraction", 0.0),
            candidate_id,
        )

    expected_selected = min(expected_front, key=tie_break)
    if report.get("selected_candidate_id") != expected_selected:
        raise ValueError("selected candidate does not match deterministic Pareto tie-break")


def _validate_multi_candidate_provenance(report: dict[str, Any]) -> None:
    """Recompute serialized candidate-source and Pareto-source audit claims."""
    provenance = report.get("provenance", {})
    if not isinstance(provenance, dict):
        raise ValueError("discovery_report provenance must be an object")

    count_key = "candidate_source_counts"
    coverage_key = "pareto_source_coverage"
    has_counts = count_key in provenance
    has_coverage = coverage_key in provenance
    if has_counts != has_coverage:
        raise ValueError("multi-candidate provenance must include both source counts and Pareto coverage")
    if not has_counts:
        return

    allowed_sources = DISCOVERY_CANDIDATE_SOURCES
    recomputed_counts: Counter[str] = Counter()
    candidate_sources: dict[str, set[str]] = {}
    for index, candidate in enumerate(report.get("candidates", [])):
        source = candidate.get("source")
        if source not in allowed_sources:
            raise ValueError(f"multi-candidate candidate[{index}] has unsupported source")
        sources = {source}
        metrics = candidate.get("metrics", {})
        source_provenance = metrics.get("source_provenance", [])
        if not isinstance(source_provenance, list):
            raise ValueError(
                f"multi-candidate candidate[{index}] source_provenance must be a list"
            )
        for provenance_index, item in enumerate(source_provenance):
            if not isinstance(item, dict) or item.get("source") not in allowed_sources:
                raise ValueError(
                    f"multi-candidate candidate[{index}] source_provenance[{provenance_index}] has invalid source"
                )
            if not isinstance(item.get("strategy"), str) or not item["strategy"].strip():
                raise ValueError(
                    f"multi-candidate candidate[{index}] source provenance needs a strategy"
                )
            sources.add(item["source"])
        candidate_sources[candidate["candidate_id"]] = sources
        for candidate_source in sources:
            recomputed_counts[candidate_source] += 1

    recorded_counts = provenance[count_key]
    if not isinstance(recorded_counts, dict):
        raise ValueError("candidate_source_counts must be an object")
    normalized_counts = {}
    for source, count in recorded_counts.items():
        if source not in allowed_sources or isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("candidate_source_counts contains an invalid source/count")
        normalized_counts[source] = count
    if normalized_counts != dict(sorted(recomputed_counts.items())):
        raise ValueError("candidate_source_counts do not match candidate source provenance")

    pareto_ids = report.get("pareto_candidate_ids", [])
    expected_pareto_sources = sorted({
        source
        for candidate_id in pareto_ids
        for source in candidate_sources.get(candidate_id, set())
    })
    recorded_coverage = provenance[coverage_key]
    if not isinstance(recorded_coverage, dict):
        raise ValueError("pareto_source_coverage must be an object")
    if recorded_coverage.get("sources") != expected_pareto_sources:
        raise ValueError("Pareto source coverage does not match candidate provenance")
    expected_both = (
        "llm_proposal" in expected_pareto_sources
        and "pysr_search" in expected_pareto_sources
    )
    if recorded_coverage.get("contains_llm_and_pysr") is not expected_both:
        raise ValueError("Pareto cross-source coverage flag does not match candidate provenance")



def _validate_candidate_envelope_audit(report: dict[str, Any]) -> None:
    """Recompute all arithmetic and completeness claims in the envelope audit."""
    provenance = report.get("provenance", {})
    if not isinstance(provenance, dict):
        raise ValueError("discovery_report provenance must be an object")
    if "candidate_envelope_audit" not in provenance:
        return

    audit = provenance["candidate_envelope_audit"]
    if not isinstance(audit, dict):
        raise ValueError("candidate_envelope_audit must be an object")
    if audit.get("schema") != "discovery_candidates_v1":
        raise ValueError("candidate_envelope_audit has unsupported schema")

    container_valid = audit.get("container_valid")
    if not isinstance(container_valid, bool):
        raise ValueError("candidate envelope container_valid must be boolean")

    def nonnegative_int(field: str, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"candidate envelope {field} must be a nonnegative integer")
        return value

    retained = nonnegative_int("retained_item_count", audit.get("retained_item_count"))
    malformed = nonnegative_int("malformed_item_count", audit.get("malformed_item_count"))
    failures = nonnegative_int("ingestion_failure_count", audit.get("ingestion_failure_count"))
    if malformed > retained:
        raise ValueError("candidate envelope malformed count exceeds retained item count")

    if container_valid:
        declared = nonnegative_int("declared_item_count", audit.get("declared_item_count"))
        if retained != declared:
            raise ValueError("candidate envelope retained count differs from declared item count")
        expected_failures = malformed
    else:
        if audit.get("declared_item_count") is not None:
            raise ValueError("invalid candidate envelope container must not claim a declared item count")
        expected_failures = 1 + malformed

    if failures != expected_failures:
        raise ValueError("candidate envelope ingestion failure count is inconsistent")

    generation_count = audit.get("generation_reported_candidate_count")
    if generation_count is not None:
        generation_count = nonnegative_int("generation_reported_candidate_count", generation_count)
    expected_count_match = (
        retained == generation_count
        if container_valid and generation_count is not None
        else None
    )
    if audit.get("count_matches_generation_metadata") is not expected_count_match:
        raise ValueError("candidate envelope generation count match flag is inconsistent")

    generation = audit.get("producer_generation")
    if generation is not None:
        if not isinstance(generation, dict):
            raise ValueError("candidate envelope producer_generation must be an object")
        def count(field: str) -> int:
            return nonnegative_int(field, generation.get(field))
        observed = count("llm_hypotheses_observed")
        admitted = count("llm_hypotheses_admitted")
        missing_llm = count("llm_hypotheses_missing_expression")
        dedup_llm = count("llm_hypotheses_deduplicated")
        raw = count("raw_proposal_count")
        unique = count("deduplicated_candidate_count")
        dedup_total = count("deduplication_count")
        missing_total = count("missing_expression_count")
        if observed != admitted + missing_llm + dedup_llm:
            raise ValueError("producer LLM proposal accounting is inconsistent")
        pysr_generated = generation.get("pysr_search_generated_candidate")
        pysr_missing = generation.get("pysr_candidate_missing_expression")
        pysr_dedup = generation.get("pysr_candidate_deduplicated")
        if not all(isinstance(value, bool) for value in (pysr_generated, pysr_missing, pysr_dedup)):
            raise ValueError("producer PySR generation flags must be boolean")
        if raw != observed + int(pysr_generated):
            raise ValueError("producer raw proposal count is inconsistent")
        if unique != retained or (generation_count is not None and unique != generation_count):
            raise ValueError("producer unique candidate count differs from retained envelope count")
        if dedup_total != dedup_llm + int(pysr_dedup):
            raise ValueError("producer deduplication count is inconsistent")
        if missing_total != missing_llm + int(pysr_missing):
            raise ValueError("producer missing-expression count is inconsistent")
        if pysr_missing and pysr_dedup:
            raise ValueError("producer PySR candidate cannot be both missing and deduplicated")
        if not pysr_generated and (pysr_dedup or pysr_missing):
            raise ValueError("producer PySR candidate accounting lacks a generated proposal")

    expected_complete = (
        container_valid and malformed == 0
        and (generation_count is None or retained == generation_count)
        and (generation is None or (
            generation.get("missing_expression_count") == 0
            and generation.get("deduplication_count") == 0
        ))
    )
    if audit.get("ingestion_complete") is not expected_complete:
        raise ValueError("candidate envelope ingestion_complete flag is inconsistent")


def _discovery_report_from_result(result: Any) -> dict[str, Any] | None:
    """Extract a typed report and validate its versioned, serialized contract."""
    if not isinstance(result, dict):
        return None
    report = result.get("discovery_report")
    if report is None and isinstance(result.get("metadata"), dict):
        report = result["metadata"].get("discovery_report")
    if report is None and isinstance(result.get("discovery"), dict):
        report = result["discovery"].get("discovery_report")
    if report is None:
        return None
    if not isinstance(report, dict):
        raise ValueError("discovery_report must be a JSON object when present")

    required = {
        "schema_version", "status", "candidates", "selected_candidate_id",
        "pareto_candidate_ids", "failure_reasons", "provenance",
        "far_evaluation", "far_evaluation_used_for_selection",
    }
    missing = sorted(required - set(report))
    if missing:
        raise ValueError(f"discovery_report missing required fields: {missing}")
    if report["schema_version"] not in DISCOVERY_REPORT_SCHEMA_VERSIONS:
        raise ValueError(
            f"unsupported discovery_report schema_version {report['schema_version']!r}"
        )
    if report["status"] not in DISCOVERY_REPORT_STATUSES:
        raise ValueError(f"unsupported discovery_report status {report['status']!r}")
    if not isinstance(report["candidates"], list):
        raise ValueError("discovery_report candidates must be a list")
    if not isinstance(report["pareto_candidate_ids"], list):
        raise ValueError("discovery_report Pareto IDs must be a list")
    if not isinstance(report["failure_reasons"], list) or any(
        not isinstance(reason, str) for reason in report["failure_reasons"]
    ):
        raise ValueError("discovery_report failure_reasons must be a list of strings")
    if not isinstance(report["provenance"], dict) or not isinstance(report["far_evaluation"], dict):
        raise ValueError("discovery_report provenance/far_evaluation must be objects")
    if report["far_evaluation_used_for_selection"] is not False:
        raise ValueError("discovery_report must declare far evaluation as unused for selection")

    ids: list[str] = []
    candidate_required = {
        "candidate_id", "expression", "normalized_expression", "source",
        "search_strategy", "seed", "constraint_outcomes", "metrics",
        "rejection_reasons", "eligible",
    }
    for index, candidate in enumerate(report["candidates"]):
        if not isinstance(candidate, dict):
            raise ValueError(f"discovery_report candidate[{index}] must be an object")
        absent = sorted(candidate_required - set(candidate))
        if absent:
            raise ValueError(f"discovery_report candidate[{index}] missing fields: {absent}")
        candidate_id = candidate["candidate_id"]
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError(f"discovery_report candidate[{index}] has invalid candidate_id")
        ids.append(candidate_id)
        for field in ("expression", "normalized_expression", "search_strategy"):
            if not isinstance(candidate[field], str) or not candidate[field].strip():
                raise ValueError(f"discovery_report candidate[{index}] {field} must be non-empty")
        if candidate["source"] not in DISCOVERY_CANDIDATE_SOURCES:
            raise ValueError(f"discovery_report candidate[{index}] has unsupported source")
        if isinstance(candidate["seed"], bool) or not isinstance(candidate["seed"], int):
            raise ValueError(f"discovery_report candidate[{index}] seed must be an integer")
        if not isinstance(candidate["constraint_outcomes"], list):
            raise ValueError(f"discovery_report candidate[{index}] constraint_outcomes must be a list")
        if not isinstance(candidate["metrics"], dict):
            raise ValueError(f"discovery_report candidate[{index}] metrics must be an object")
        if not isinstance(candidate["rejection_reasons"], list) or any(
            not isinstance(reason, str) for reason in candidate["rejection_reasons"]
        ):
            raise ValueError(f"discovery_report candidate[{index}] rejection_reasons must be strings")
        if not isinstance(candidate["eligible"], bool):
            raise ValueError(f"discovery_report candidate[{index}] eligible must be boolean")
        for outcome_index, outcome in enumerate(candidate["constraint_outcomes"]):
            if not isinstance(outcome, dict):
                raise ValueError(
                    f"discovery_report candidate[{index}] constraint_outcomes[{outcome_index}] must be an object"
                )
            if not isinstance(outcome.get("constraint_id"), str) or not outcome["constraint_id"]:
                raise ValueError("discovery_report constraint outcome needs a constraint_id")
            if outcome.get("status") not in DISCOVERY_CONSTRAINT_STATUSES:
                raise ValueError("discovery_report constraint outcome has unsupported status")
            if outcome.get("severity") not in {"hard", "soft"}:
                raise ValueError("discovery_report constraint outcome has unsupported severity")
            if not isinstance(outcome.get("reason"), str) or not isinstance(outcome.get("evidence"), dict):
                raise ValueError("discovery_report constraint outcome reason/evidence have invalid types")

    _validate_multi_candidate_provenance(report)
    _validate_candidate_envelope_audit(report)
    _validate_soft_constraint_pareto_contract(report)
    _validate_pareto_selection_consistency(report)

    if len(ids) != len(set(ids)):
        raise ValueError("discovery_report candidate records must have unique candidate IDs")
    selected_id = report["selected_candidate_id"]
    if selected_id is not None and (not isinstance(selected_id, str) or selected_id not in ids):
        raise ValueError("discovery_report selected candidate is absent from candidate records")
    pareto_ids = report["pareto_candidate_ids"]
    if any(not isinstance(item, str) for item in pareto_ids) or len(pareto_ids) != len(set(pareto_ids)):
        raise ValueError("discovery_report Pareto IDs must be unique strings")
    if not set(pareto_ids).issubset(set(ids)):
        raise ValueError("discovery_report Pareto IDs are absent from candidate records")
    if selected_id is not None and selected_id not in pareto_ids:
        raise ValueError("discovery_report selected candidate must belong to the Pareto set")
    if report["status"] in {
        "no_credible_candidate", "invalid_problem_specification",
        "no_candidates_generated", "all_candidates_failed_symbolic_validation",
        "all_candidates_failed_physical_gates", "insufficient_validation_evidence",
        "search_budget_exhausted",
    } and selected_id is not None:
        raise ValueError("discovery_report failure status cannot carry a selected candidate")
    return report

def validate_worker_outputs(
    output_dir: Path,
    run_start_marker: Path,
    expected_domains: list[str],
) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    marker_time = run_start_marker.stat().st_mtime
    expected_domains = [domain for domain in expected_domains if domain]
    if not expected_domains or len(expected_domains) != len(set(expected_domains)):
        raise ValueError("expected domains must be non-empty and unique")

    protocol_files = sorted(
        path for path in output_dir.glob("protocol_core_extrap_*.json")
        if path.stat().st_mtime > marker_time
    )
    if len(protocol_files) != len(expected_domains):
        raise ValueError(
            f"expected one current-run protocol file per assigned domain "
            f"({len(expected_domains)}), found {len(protocol_files)}"
        )

    expected_domain_set = set(expected_domains)
    expected_identities: set[tuple[str, str, str]] = set()
    methods_reference: list[str] | None = None
    equation_domains: set[str] = set()
    protocol_manifest: list[dict[str, Any]] = []
    discovery_report_records: list[dict[str, Any]] = []
    expected_discovery_report_identities: set[tuple[str, str, str]] = set()
    hybrid_discovery_report_count = 0

    for protocol_path in protocol_files:
        protocol = _load_strict_json(protocol_path)
        methods = protocol.get("methods")
        tests = protocol.get("tests")
        if not isinstance(methods, list) or len(methods) != EXPECTED_METHOD_COUNT:
            raise ValueError(f"{protocol_path.name}: expected {EXPECTED_METHOD_COUNT} methods")
        if len(methods) != len(set(methods)):
            raise ValueError(f"{protocol_path.name}: duplicate method names")
        if methods_reference is None:
            methods_reference = methods
        elif methods != methods_reference:
            raise ValueError(f"{protocol_path.name}: method roster differs between domains")
        if not isinstance(tests, list) or not tests:
            raise ValueError(f"{protocol_path.name}: tests must be a non-empty list")
        if protocol.get("total_tests") != len(tests):
            raise ValueError(
                f"{protocol_path.name}: total_tests={protocol.get('total_tests')} "
                f"but tests has {len(tests)} records"
            )

        file_domains: set[str] = set()
        for test in tests:
            domain = str(test.get("domain") or "")
            description = str(test.get("description") or "")
            if not domain or not description:
                raise ValueError(f"{protocol_path.name}: test missing domain/description")
            if domain not in expected_domain_set:
                raise ValueError(
                    f"{protocol_path.name}: unexpected domain {domain!r}; "
                    f"expected {sorted(expected_domain_set)}"
                )
            file_domains.add(domain)
            equation_domains.add(domain)

            results = test.get("results")
            far_r2 = test.get("extrap_r2_far")
            far_rmse = test.get("extrap_rmse_far")
            if not isinstance(results, dict) or set(results) != set(methods):
                raise ValueError(f"{protocol_path.name}: {description!r} has incomplete method results")
            if not isinstance(far_r2, dict) or set(far_r2) != set(methods):
                raise ValueError(f"{protocol_path.name}: {description!r} has incomplete far-R2 map")
            if not isinstance(far_rmse, dict) or set(far_rmse) != set(methods):
                raise ValueError(f"{protocol_path.name}: {description!r} has incomplete far-RMSE map")
            if int(test.get("extrap_n_train") or 0) < 2:
                raise ValueError(f"{protocol_path.name}: {description!r} has fewer than 2 train rows")
            if int(test.get("extrap_n_test") or 0) < 2:
                raise ValueError(f"{protocol_path.name}: {description!r} has fewer than 2 far rows")

            for method in methods:
                result = results[method]
                if not isinstance(result.get("success"), bool):
                    raise ValueError(
                        f"{protocol_path.name}: {description!r}/{method} missing success boolean"
                    )
                expected_identities.add((domain, description, method))
                report = _discovery_report_from_result(result)
                if method == REQUIRED_DISCOVERY_REPORT_METHOD:
                    identity = (domain, description, method)
                    expected_discovery_report_identities.add(identity)
                    if report is None:
                        raise ValueError(
                            f"{protocol_path.name}: {description!r}/{method} "
                            "completed without the required DiscoveryReport"
                        )
                    result_metadata = result.get("metadata", {})
                    if not isinstance(result_metadata, dict):
                        raise ValueError(
                            f"{protocol_path.name}: {description!r}/{method} "
                            "has no structured result metadata"
                        )
                    contract_audit = result_metadata.get(
                        "discovery_problem_contract", {}
                    )
                    if not isinstance(contract_audit, dict) or contract_audit.get("active") is not True:
                        raise ValueError(
                            f"{protocol_path.name}: {description!r}/{method} "
                            "did not activate the typed DiscoveryProblem contract"
                        )
                    hybrid_discovery_report_count += 1
                if report is not None:
                    discovery_report_records.append({
                        "domain": domain,
                        "equation": description,
                        "method": method,
                        "protocol_file": protocol_path.name,
                        "discovery_report": report,
                    })

        if len(file_domains) != 1:
            raise ValueError(
                f"{protocol_path.name}: protocol file must represent exactly one domain, "
                f"found {sorted(file_domains)}"
            )
        protocol_manifest.append({
            "file": protocol_path.name,
            "sha256": _sha256(protocol_path),
            "bytes": protocol_path.stat().st_size,
            "domain": next(iter(file_domains)),
            "equations": len(tests),
        })

    if equation_domains != expected_domain_set:
        raise ValueError(
            f"protocol domain coverage mismatch: expected {sorted(expected_domain_set)}, "
            f"found {sorted(equation_domains)}"
        )

    if len(expected_discovery_report_identities) != hybrid_discovery_report_count:
        raise ValueError(
            "required HybridDiscovery DiscoveryReport coverage mismatch: "
            f"expected {len(expected_discovery_report_identities)}, "
            f"found {hybrid_discovery_report_count} records"
        )

    benchmark_path = output_dir / "benchmark_results_extrap.json"
    if not benchmark_path.is_file() or benchmark_path.stat().st_mtime <= marker_time:
        raise ValueError("benchmark_results_extrap.json was not produced by the current run")
    benchmark_rows = _load_strict_json(benchmark_path)
    if not isinstance(benchmark_rows, list):
        raise ValueError("benchmark_results_extrap.json must contain a JSON list")

    row_counts: Counter[tuple[str, str, str]] = Counter()
    for row in benchmark_rows:
        identity = (
            str(row.get("domain") or ""),
            str(row.get("test") or ""),
            str(row.get("method") or ""),
        )
        if not all(identity):
            raise ValueError("benchmark row missing domain/test/method identity")
        row_counts[identity] += 1
        if identity in expected_identities:
            if not isinstance(row.get("success"), bool):
                raise ValueError(f"current-run row {identity} missing success boolean")
            if "extrap_r2_far" not in row or "extrap_rmse_far" not in row:
                raise ValueError(f"current-run row {identity} missing far-region metrics")

    missing = sorted(identity for identity in expected_identities if row_counts[identity] == 0)
    duplicated = sorted(identity for identity in expected_identities if row_counts[identity] != 1 and row_counts[identity] > 1)
    if missing:
        raise ValueError(f"benchmark flat output missing {len(missing)} expected method/equation rows")
    if duplicated:
        raise ValueError(f"benchmark flat output duplicates {len(duplicated)} expected method/equation rows")

    report_path = output_dir / "discovery_reports_extrap.json"
    report_artifact = {
        "schema_version": "exp2_discovery_report_artifact_v1",
        "report_count": len(discovery_report_records),
        "records": discovery_report_records,
        "selection_boundary": {
            "selection_data_scope": "training_region_only",
            "far_evaluation_used_for_selection": False,
        },
    }
    report_path.write_text(
        json.dumps(report_artifact, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "step": "exp2_feynman_extrap",
        "worker_outputs_complete": True,
        "status": "complete",
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "git_sha": os.environ.get("GITHUB_SHA"),
        "shard": os.environ.get("SHARD_INDEX", os.environ.get("SHARD")),
        "expected_domains": expected_domains,
        "method_count": len(methods_reference or []),
        "equation_count": len(expected_identities) // EXPECTED_METHOD_COUNT,
        "expected_method_equation_rows": len(expected_identities),
        "benchmark_row_count": len(benchmark_rows),
        "protocol_files": protocol_manifest,
        "discovery_report_artifact": {
            "file": report_path.name,
            "sha256": _sha256(report_path),
            "bytes": report_path.stat().st_size,
            "report_count": len(discovery_report_records),
            "status": "present" if discovery_report_records else "no_typed_discovery_reports",
        },
        "benchmark_file": {
            "file": benchmark_path.name,
            "sha256": _sha256(benchmark_path),
            "bytes": benchmark_path.stat().st_size,
        },
        "post_run_analysis": {
            "repository": "sednabcn/LLM-HypatiaX-DEV",
            "status": "delegated_to_post_run_repository",
        },
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-start-marker", type=Path, required=True)
    parser.add_argument("--expected-domains", required=True)
    parser.add_argument("--summary-name", default="exp2_extrap_summary.json")
    args = parser.parse_args()

    domains = args.expected_domains.split()
    summary = validate_worker_outputs(args.output_dir, args.run_start_marker, domains)
    summary_path = args.output_dir / args.summary_name
    summary_path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        f"[exp2-extrap-validation] complete: domains={len(summary['expected_domains'])}, "
        f"equations={summary['equation_count']}, methods={summary['method_count']}, "
        f"method-equation rows={summary['expected_method_equation_rows']}, discovery reports={summary['discovery_report_artifact']['report_count']}"
    )
    print(f"[exp2-extrap-validation] manifest: {summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        raise SystemExit(f"::error::Exp2 extrapolation output validation failed: {exc}")
