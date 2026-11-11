#!/usr/bin/env python3
"""Validate the pre-run tau calibration manifest without executing experiments.

The default mode checks structure and approved protocol constants. --require-ready
additionally rejects placeholders and incomplete calibration design. This tool
never computes tau, reads benchmark outcomes, or launches model/compute jobs.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


APPROVED = {
    "edge_r2_floor": 0.99,
    "relative_margin": 0.0,
    "bad_routing_risk": 0.05,
    "one_sided_confidence": 0.95,
    "minimum_n_if_zero_failures": 59,
}


def extract_core15_ids(source_text: str) -> list[str]:
    """Extract equation names from the literal CORE_15 catalogue block."""
    start = source_text.find("CORE_15 = [")
    if start < 0:
        raise ValueError("CORE_15 catalogue not found")
    end = source_text.find("# Stable ID map", start)
    if end < 0:
        raise ValueError("CORE_15 catalogue terminator not found")
    block = source_text[start:end]
    names = re.findall(r'"name"\s*:\s*"([^"]+)"', block)
    if len(names) != 15 or len(set(names)) != 15:
        raise ValueError(
            f"Expected 15 unique Core-15 equation names; found {len(names)}"
        )
    return names


def validate_manifest(
    manifest: dict[str, Any],
    core15_ids: list[str],
    *,
    require_ready: bool = False,
) -> list[str]:
    """Return validation errors; an empty list means the requested checks pass."""
    errors: list[str] = []
    protocol = manifest.get("approved_protocol", {})
    for key, expected in APPROVED.items():
        actual = protocol.get(key)
        if actual != expected:
            errors.append(f"approved_protocol.{key} must equal {expected!r}")

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    declared_exclusions = manifest.get("core15_exclusion_ids")
    if declared_exclusions != core15_ids:
        errors.append(
            "core15_exclusion_ids must exactly match the current CORE_15 catalogue "
            "in source order"
        )

    equations = manifest.get("calibration_equations")
    if not isinstance(equations, list):
        errors.append("calibration_equations must be a list")
        equations = []
    seen_ids: set[str] = set()
    units_by_category: dict[str, set[str]] = defaultdict(set)
    seen_units_globally: set[str] = set()
    counts_by_category: dict[str, int] = defaultdict(int)
    for index, item in enumerate(equations):
        prefix = f"calibration_equations[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        equation_id = item.get("equation_id")
        category = item.get("category")
        unit_id = item.get("independent_unit_id")
        provenance = item.get("provenance")
        if not isinstance(equation_id, str) or not equation_id.strip():
            errors.append(f"{prefix}.equation_id must be a non-empty string")
        elif equation_id in seen_ids:
            errors.append(f"duplicate calibration equation_id: {equation_id}")
        else:
            seen_ids.add(equation_id)
        if equation_id in core15_ids:
            errors.append(f"Core-15 leakage: {equation_id}")
        if not isinstance(category, str) or not category.strip():
            errors.append(f"{prefix}.category must be a non-empty string")
        if not isinstance(unit_id, str) or not unit_id.strip():
            errors.append(f"{prefix}.independent_unit_id must be a non-empty string")
        elif isinstance(category, str) and category.strip():
            if unit_id in seen_units_globally:
                errors.append(
                    f"independent_unit_id {unit_id!r} is reused; units must be "
                    "unique across the entire calibration manifest"
                )
            seen_units_globally.add(unit_id)
            units_by_category[category].add(unit_id)
        if not isinstance(provenance, str) or not provenance.strip():
            errors.append(f"{prefix}.provenance must identify an auditable source")
        if item.get("uses_training_data_only") is not True:
            errors.append(f"{prefix}.uses_training_data_only must be true")
        forbidden = {
            "heldout_targets", "heldout_scores", "extrapolation_scores",
            "core15_outcomes", "test_labels",
        }.intersection(item)
        if forbidden:
            errors.append(f"{prefix} contains forbidden fields: {sorted(forbidden)}")
        if isinstance(category, str) and category.strip():
            counts_by_category[category] += 1

    candidates = manifest.get("candidate_tau_values")
    if not isinstance(candidates, list):
        errors.append("candidate_tau_values must be a list")
        candidates = []
    normalized: list[float] = []
    for value in candidates:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append("candidate_tau_values must contain finite non-negative numbers")
            continue
        number = float(value)
        if not math.isfinite(number) or number < 0:
            errors.append("candidate_tau_values must contain finite non-negative numbers")
        elif number in normalized:
            errors.append(f"duplicate candidate tau value: {number}")
        else:
            normalized.append(number)

    selection = manifest.get("selection_procedure", {})
    selection_name = selection.get("name") if isinstance(selection, dict) else None
    if require_ready:
        if manifest.get("status") != "ready_for_calibration":
            errors.append("status must be ready_for_calibration")
        if not equations:
            errors.append("at least one predeclared calibration equation is required")
        if not candidates:
            errors.append("at least one predeclared candidate tau is required")
        if not isinstance(selection_name, str) or not selection_name.strip() or selection_name == "NOT_SELECTED":
            errors.append("a concrete selection-aware risk-control procedure must be selected")
        if isinstance(selection, dict) and not selection.get("implementation_or_spec_ref"):
            errors.append("selection procedure must include implementation_or_spec_ref")
        if not manifest.get("independence_justification"):
            errors.append("independence_justification is required")
        if not manifest.get("category_definition"):
            errors.append("category_definition is required")
        if not manifest.get("frozen_edge_definition"):
            errors.append("frozen_edge_definition is required")
        for key in ("calibration_data_manifest_sha256",):
            value = manifest.get(key)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                errors.append(f"{key} must be a 64-character lowercase SHA-256")
        for key in ("calibration_code_commit", "evaluator_version"):
            value = manifest.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{key} must be recorded before calibration")
        for index, item in enumerate(equations):
            if not isinstance(item, dict):
                continue
            for key in ("source_sha256", "formula_sha256", "training_rows_sha256"):
                value = item.get(key)
                if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                    errors.append(
                        f"calibration_equations[{index}].{key} must be a 64-character lowercase SHA-256"
                    )
            source_ref = item.get("source_ref")
            if not isinstance(source_ref, str) or not source_ref.strip():
                errors.append(f"calibration_equations[{index}].source_ref is required")
        underpowered = {
            category: count for category, count in counts_by_category.items()
            if count < APPROVED["minimum_n_if_zero_failures"]
        }
        if underpowered:
            errors.append(
                "each category needs at least 59 independent units even in the "
                f"zero-failure case; found {underpowered}"
            )
    elif manifest.get("status") not in {"draft", "ready_for_calibration"}:
        errors.append("status must be draft or ready_for_calibration")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("config/tau_calibration_manifest.json"),
    )
    parser.add_argument(
        "--core15-source", type=Path,
        default=Path("hypatiax/experiments/benchmarks/exp1_ablation.py"),
    )
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        core15_ids = extract_core15_ids(
            args.core15_source.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}")
        return 2

    errors = validate_manifest(
        manifest, core15_ids, require_ready=args.require_ready
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"INVALID ({len(errors)} issue(s))")
        return 1
    print(
        "STRUCTURE VALID; calibration readiness not established."
        if not args.require_ready
        else "READY CHECK PASSED; no calibration or experiment was executed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
