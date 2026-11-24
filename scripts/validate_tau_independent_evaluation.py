#!/usr/bin/env python3
"""Validate frozen, family-disjoint tau evaluation outcomes offline.

This validator makes no provider calls and does not select or retune tau. It
checks cohort disjointness and applies the exact one-sided binomial risk test
to the routes accepted by the already-frozen threshold in each category.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


APPROVED = {
    "edge_r2_floor": 0.99,
    "relative_margin": 0.0,
    "tolerated_bad_route_rate_epsilon": 0.05,
    "family_wise_error_delta": 0.05,
    "one_sided_confidence": 0.95,
    "minimum_n_if_zero_failures": 59,
}
EVALUATOR_VERSION = "tau-independent-evaluation-validator-v1"


def extract_core15_ids(source_text: str) -> list[str]:
    start = source_text.find("CORE_15 = [")
    if start < 0:
        raise ValueError("CORE_15 catalogue not found")
    end = source_text.find("# Stable ID map", start)
    if end < 0:
        raise ValueError("CORE_15 catalogue terminator not found")
    names = re.findall(r'"name"\\s*:\\s*"([^"]+)"', source_text[start:end])
    if len(names) != 15 or len(set(names)) != 15:
        raise ValueError(f"Expected 15 unique Core-15 names; found {len(names)}")
    return names


def _binomial_lower_tail(k: int, n: int, p: float) -> float:
    """Return P[X <= k] for X~Binomial(n,p), using log-sum-exp."""
    if n <= 0 or k < 0 or k > n or not 0.0 < p < 1.0:
        raise ValueError("invalid binomial arguments")
    terms = [
        math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
        + j * math.log(p) + (n - j) * math.log1p(-p)
        for j in range(k + 1)
    ]
    maximum = max(terms)
    return min(1.0, math.exp(maximum) * sum(math.exp(x - maximum) for x in terms))


def exact_bad_route_test(bad_routes: int, accepted_routes: int) -> dict[str, Any]:
    """Test H0:p_bad >= epsilon against p_bad < epsilon at level delta."""
    if accepted_routes <= 0 or not 0 <= bad_routes <= accepted_routes:
        return {
            "certified": False,
            "p_value": None,
            "reason": "no_accepted_routes" if accepted_routes == 0 else "invalid_bad_route_count",
        }
    epsilon = APPROVED["tolerated_bad_route_rate_epsilon"]
    delta = APPROVED["family_wise_error_delta"]
    p_value = _binomial_lower_tail(bad_routes, accepted_routes, epsilon)
    return {
        "certified": p_value <= delta,
        "p_value": p_value,
        "reason": None if p_value <= delta else "bad_route_risk_not_certified",
    }


def _string_list(value: Any, field: str, errors: list[str], *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        errors.append(f"{field} must be a {'non-empty ' if nonempty else ''}list of strings")
        return []
    if any(not isinstance(x, str) or not x.strip() for x in value):
        errors.append(f"{field} must contain only non-empty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{field} must not contain duplicates")
    return value


def validate_evaluation(
    payload: dict[str, Any],
    core15_ids: list[str],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    protocol = payload.get("approved_protocol")
    if not isinstance(protocol, dict):
        errors.append("approved_protocol must be an object")
        protocol = {}
    for key, expected in APPROVED.items():
        if protocol.get(key) != expected:
            errors.append(f"approved_protocol.{key} must equal {expected!r}")

    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("status") != "evaluation_complete":
        errors.append("status must be evaluation_complete")
    for field in (
        "evaluation_manifest_sha256",
        "calibration_manifest_sha256",
        "historical_74_registry_sha256",
    ):
        value = payload.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            errors.append(f"{field} must be a 64-character lowercase SHA-256")
    for field in ("calibration_code_commit", "evaluation_code_commit", "evaluator_version"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be recorded")

    calibration_ids = set(_string_list(
        payload.get("calibration_family_ids"), "calibration_family_ids", errors
    ))
    historical_ids = set(_string_list(
        payload.get("historical_74_family_ids"), "historical_74_family_ids", errors
    ))
    declared_core15 = payload.get("core15_exclusion_ids")
    if declared_core15 != core15_ids:
        errors.append("core15_exclusion_ids must exactly match the current Core-15 catalogue")

    categories = _string_list(payload.get("category_list"), "category_list", errors)
    selected = payload.get("selected_tau_by_category")
    if not isinstance(selected, dict):
        errors.append("selected_tau_by_category must be an object")
        selected = {}
    if set(selected) != set(categories):
        errors.append("selected_tau_by_category keys must exactly match category_list")
    clean_tau: dict[str, float] = {}
    for category, value in selected.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"selected tau for {category!r} must be finite and non-negative")
            continue
        number = float(value)
        if not math.isfinite(number) or number < 0:
            errors.append(f"selected tau for {category!r} must be finite and non-negative")
        else:
            clean_tau[category] = number

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append("records must be a non-empty list")
        records = []

    seen_equations: set[str] = set()
    seen_families: set[str] = set()
    by_category: dict[str, list[dict[str, Any]]] = {category: [] for category in categories}
    required_review = {
        "family_review_status": "adjudicated",
        "formula_equivalence_review_status": "complete",
        "core15_overlap_status": "clear",
        "historical_74_overlap_status": "clear",
        "cross_registry_overlap_status": "clear",
        "independence_status": "independent",
    }
    for index, row in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        equation_id = row.get("equation_id")
        family_id = row.get("canonical_equation_family_id")
        unit_id = row.get("independent_unit_id")
        category = row.get("category")
        if not isinstance(equation_id, str) or not equation_id.strip():
            errors.append(f"{prefix}.equation_id must be non-empty")
        elif equation_id in seen_equations:
            errors.append(f"duplicate evaluation equation_id: {equation_id}")
        else:
            seen_equations.add(equation_id)
        if not isinstance(family_id, str) or not family_id.strip():
            errors.append(f"{prefix}.canonical_equation_family_id must be non-empty")
        else:
            if family_id in seen_families:
                errors.append(f"evaluation family reused: {family_id}")
            seen_families.add(family_id)
            if family_id in calibration_ids:
                errors.append(f"calibration/evaluation family overlap: {family_id}")
            if family_id in historical_ids:
                errors.append(f"historical-74/evaluation family overlap: {family_id}")
        if unit_id != family_id:
            errors.append(f"{prefix}.independent_unit_id must equal canonical_equation_family_id")
        if equation_id in core15_ids or family_id in core15_ids:
            errors.append(f"Core-15/evaluation overlap: {equation_id!r} / {family_id!r}")
        if category not in categories:
            errors.append(f"{prefix}.category is not in category_list")
        for field, expected in required_review.items():
            if row.get(field) != expected:
                errors.append(f"{prefix}.{field} must be {expected!r}")
        for field in ("family_review_reference", "independence_justification", "source_ref"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.{field} must be non-empty")
        for field in ("source_sha256", "formula_sha256", "training_rows_sha256"):
            value = row.get(field)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                errors.append(f"{prefix}.{field} must be a 64-character lowercase SHA-256")

        eligible = row.get("llm_eligible")
        if not isinstance(eligible, bool):
            errors.append(f"{prefix}.llm_eligible must be boolean")
            continue
        delta_llm = row.get("delta_llm")
        if eligible and (
            isinstance(delta_llm, bool)
            or not isinstance(delta_llm, (int, float))
            or not math.isfinite(float(delta_llm))
        ):
            errors.append(f"{prefix}.delta_llm must be finite for eligible rows")
            continue
        if category in by_category:
            by_category[category].append({
                "equation_id": equation_id,
                "family_id": family_id,
                "eligible": eligible,
                "delta_llm": float(delta_llm) if eligible else None,
                "bad_route": row.get("bad_route"),
            })

    report_categories: dict[str, Any] = {}
    for category in categories:
        tau = clean_tau.get(category)
        group = by_category[category]
        if not group:
            errors.append(f"category {category!r} has no evaluation records")
            continue
        accepted = [
            row for row in group
            if tau is not None and row["eligible"] and row["delta_llm"] <= tau
        ]
        bad_values = [row["bad_route"] for row in accepted]
        if any(not isinstance(value, bool) for value in bad_values):
            errors.append(
                f"category {category!r}: every accepted route needs a precomputed boolean bad_route label"
            )
            continue
        bad = sum(bad_values)
        test = exact_bad_route_test(bad, len(accepted))
        report_categories[category] = {
            "assigned_independent_families": len(group),
            "eligible_families": sum(row["eligible"] for row in group),
            "accepted_routes": len(accepted),
            "bad_routes": bad,
            "bad_route_rate": bad / len(accepted) if accepted else None,
            **test,
        }

    all_certified = (
        len(report_categories) == len(categories)
        and all(item["certified"] for item in report_categories.values())
    )
    report = {
        "evaluator_version": EVALUATOR_VERSION,
        "status": "risk_certified_on_independent_evaluation" if all_certified and not errors
                  else "not_certified_or_invalid",
        "generalization_claim": bool(all_certified and not errors),
        "categories": report_categories,
        "interpretation": (
            "The frozen tau was evaluated without retuning. Certification is per category; "
            "this does not provide a simultaneous all-category guarantee or justify changing tau."
        ),
    }
    return errors, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--core15-source", type=Path,
                        default=Path("hypatiax/experiments/benchmarks/exp1_ablation.py"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        core15 = extract_core15_ids(args.core15_source.read_text(encoding="utf-8"))
        errors, report = validate_evaluation(payload, core15)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n",
                               encoding="utf-8")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(json.dumps(report, indent=2))
    return 0 if report["generalization_claim"] and not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
