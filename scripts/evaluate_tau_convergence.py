#!/usr/bin/env python3
"""Offline convergence/stability evaluator for frozen LLM tau calibration records.

This tool makes no provider calls and does not generate formulas. It consumes
per-independent-family outcomes produced by the frozen LLM edge evaluator.
Bad-route labels must be computed by that evaluator using the ratified edge
quality and ensemble-comparison definition; this script deliberately does not
reimplement an underspecified ensemble-margin rule.

Calibration selection uses the repository-approved fixed-sequence exact
one-sided binomial procedure. Bootstrap threshold variability and local route
sensitivity are diagnostics only; they do not replace the exact risk test.
"""
from __future__ import annotations

import argparse
import json
import math
import random
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
EVALUATOR_VERSION = "tau-convergence-evaluator-v1"


def _binomial_lower_tail(k: int, n: int, p: float) -> float:
    """P[X <= k] for X~Binomial(n,p), evaluated with stable log terms."""
    if n < 0 or k < 0 or k > n or not 0.0 < p < 1.0:
        raise ValueError("invalid binomial arguments")
    terms = []
    for j in range(k + 1):
        log_term = (
            math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
            + j * math.log(p) + (n - j) * math.log1p(-p)
        )
        terms.append(log_term)
    maximum = max(terms)
    return min(1.0, math.exp(maximum) * sum(math.exp(x - maximum) for x in terms))


def exact_bad_route_test(bad: int, accepted: int, epsilon: float, delta: float) -> dict:
    """Certify p_bad < epsilon with an exact one-sided test at level delta."""
    if accepted <= 0 or bad < 0 or bad > accepted:
        return {"certified": False, "p_value": None, "reason": "no_accepted_units"}
    p_value = _binomial_lower_tail(bad, accepted, epsilon)
    return {
        "certified": bool(p_value <= delta),
        "p_value": float(p_value),
        "reason": None if p_value <= delta else "risk_not_certified",
    }


def select_threshold(
    rows: list[dict], candidates: list[float], epsilon: float, delta: float
) -> dict:
    """Apply strictest-to-laxest fixed-sequence testing within one category."""
    trace = []
    last_passed = None
    stopped = False
    for tau in candidates:
        accepted = [
            row for row in rows
            if row["llm_eligible"] and row["delta_llm"] <= tau
        ]
        bad = sum(bool(row["bad_route"]) for row in accepted)
        test = exact_bad_route_test(bad, len(accepted), epsilon, delta)
        item = {
            "tau": float(tau),
            "accepted_n": len(accepted),
            "bad_routes": int(bad),
            "bad_route_rate": (bad / len(accepted)) if accepted else None,
            **test,
        }
        trace.append(item)
        if not test["certified"]:
            stopped = True
            break
        last_passed = float(tau)
    return {
        "selected_tau": last_passed,
        "selection_status": "certified" if last_passed is not None else "no_certified_threshold",
        "stopped_at_first_failure": stopped,
        "candidate_trace": trace,
    }


def _validate_input(payload: dict[str, Any]) -> tuple[list[dict], list[float], list[str], list[str]]:
    errors: list[str] = []
    protocol = payload.get("approved_protocol", {})
    for key, expected in APPROVED.items():
        if protocol.get(key) != expected:
            errors.append(f"approved_protocol.{key} must equal {expected!r}")

    candidates = payload.get("candidate_tau_values")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidate_tau_values must be a non-empty list")
        candidates = []
    clean_candidates = []
    for value in candidates:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append("candidate tau values must be finite non-negative numbers")
            continue
        value = float(value)
        if not math.isfinite(value) or value < 0:
            errors.append("candidate tau values must be finite non-negative numbers")
        else:
            clean_candidates.append(value)
    if clean_candidates != sorted(set(clean_candidates)):
        errors.append("candidate_tau_values must be unique and strictly increasing")

    categories = payload.get("category_list")
    if not isinstance(categories, list) or not categories or any(
        not isinstance(x, str) or not x.strip() for x in categories
    ):
        errors.append("category_list must be a non-empty list of category names")
        categories = []
    if len(categories) != len(set(categories)):
        errors.append("category_list must not contain duplicates")

    rows = payload.get("records")
    if not isinstance(rows, list):
        errors.append("records must be a list")
        rows = []
    seen_equations: set[str] = set()
    seen_units: set[str] = set()
    normalized: list[dict] = []
    for i, row in enumerate(rows):
        prefix = f"records[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        equation_id = row.get("equation_id")
        unit_id = row.get("independent_unit_id")
        category = row.get("category")
        if not isinstance(equation_id, str) or not equation_id.strip():
            errors.append(f"{prefix}.equation_id must be non-empty")
        elif equation_id in seen_equations:
            errors.append(f"duplicate equation_id: {equation_id}")
        else:
            seen_equations.add(equation_id)
        if not isinstance(unit_id, str) or not unit_id.strip():
            errors.append(f"{prefix}.independent_unit_id must be non-empty")
        elif unit_id in seen_units:
            errors.append(f"independent unit reused: {unit_id}")
        else:
            seen_units.add(unit_id)
        if category not in categories:
            errors.append(f"{prefix}.category is not in category_list: {category!r}")
        eligible = row.get("llm_eligible")
        if not isinstance(eligible, bool):
            errors.append(f"{prefix}.llm_eligible must be boolean")
            continue
        delta_value = row.get("delta_llm")
        bad_route = row.get("bad_route")
        if eligible:
            if isinstance(delta_value, bool) or not isinstance(delta_value, (int, float)) or not math.isfinite(float(delta_value)):
                errors.append(f"{prefix}.delta_llm must be finite when llm_eligible is true")
                continue
            if not isinstance(bad_route, bool):
                errors.append(f"{prefix}.bad_route must be boolean for eligible rows")
                continue
        normalized.append({
            "equation_id": equation_id,
            "independent_unit_id": unit_id,
            "category": category,
            "llm_eligible": eligible,
            "delta_llm": float(delta_value) if eligible else None,
            "bad_route": bool(bad_route) if eligible else False,
            "status": row.get("status", "unspecified"),
        })
    if set(categories) - {r.get("category") for r in normalized}:
        errors.append("one or more declared categories have no records")
    return normalized, clean_candidates, categories, errors


def _route_set(rows: list[dict], tau: float) -> set[str]:
    return {
        row["independent_unit_id"] for row in rows
        if row["llm_eligible"] and row["delta_llm"] <= tau
    }


def _bootstrap_stability(
    rows: list[dict], candidates: list[float], epsilon: float, delta: float,
    replicates: int, seed: int,
) -> dict:
    if replicates <= 0:
        return {"replicates": 0, "available": False, "reason": "bootstrap_disabled"}
    if len(rows) < 2:
        return {"replicates": replicates, "available": False, "reason": "fewer_than_two_families"}
    rng = random.Random(seed)
    selected: list[float | None] = []
    for _ in range(replicates):
        sample = [rows[rng.randrange(len(rows))] for _ in range(len(rows))]
        selected.append(select_threshold(sample, candidates, epsilon, delta)["selected_tau"])
    finite = sorted(x for x in selected if x is not None)
    counts = {str(t): selected.count(t) for t in candidates}
    counts["unselected"] = selected.count(None)
    if not finite:
        interval = None
    else:
        lo = finite[max(0, math.ceil(0.025 * len(finite)) - 1)]
        hi = finite[min(len(finite) - 1, math.ceil(0.975 * len(finite)) - 1)]
        interval = [lo, hi]
    return {
        "replicates": replicates,
        "available": True,
        "seed": seed,
        "selected_tau_counts": counts,
        "unselected_fraction": selected.count(None) / replicates,
        "conditional_percentile_interval_95": interval,
        "note": "Diagnostic only; interval is conditional on selected replicates and is not the exact risk guarantee.",
    }


def _sensitivity(rows: list[dict], tau: float, perturbation: float) -> dict:
    eligible = [r for r in rows if r["llm_eligible"]]
    base = _route_set(rows, tau)
    lower = _route_set(rows, max(0.0, tau - perturbation))
    upper = _route_set(rows, tau + perturbation)
    denominator = len(eligible)
    def fraction(changed: set[str]) -> float | None:
        return len(changed) / denominator if denominator else None
    return {
        "perturbation": perturbation,
        "eligible_units": denominator,
        "route_flip_fraction_tau_minus": fraction(base.symmetric_difference(lower)),
        "route_flip_fraction_tau_plus": fraction(base.symmetric_difference(upper)),
        "routes_at_tau": len(base),
        "routes_at_tau_minus": len(lower),
        "routes_at_tau_plus": len(upper),
        "decision_stability": "not_assessable" if not denominator else "measured",
    }


def evaluate(payload: dict[str, Any], *, bootstrap_replicates: int = 2000,
             seed: int = 20261123, tau_perturbation: float = 0.01) -> dict:
    rows, candidates, categories, errors = _validate_input(payload)
    if errors:
        raise ValueError("input validation failed:\n- " + "\n- ".join(errors))
    if not math.isfinite(tau_perturbation) or tau_perturbation < 0:
        raise ValueError("tau_perturbation must be finite and non-negative")

    epsilon = APPROVED["tolerated_bad_route_rate_epsilon"]
    delta = APPROVED["family_wise_error_delta"]
    minimum_n = APPROVED["minimum_n_if_zero_failures"]
    results = {}
    for index, category in enumerate(categories):
        group = [row for row in rows if row["category"] == category]
        eligible = [row for row in group if row["llm_eligible"]]
        n_units = len({row["independent_unit_id"] for row in group})
        summary = {
            "assigned_independent_units": n_units,
            "eligible_units": len(eligible),
            "eligibility_coverage": len(eligible) / n_units if n_units else None,
            "ineligible_or_failed_units": n_units - len(eligible),
            "minimum_units_met": n_units >= minimum_n,
        }
        if n_units < minimum_n:
            summary.update({
                "selection_status": "insufficient_evidence",
                "selected_tau": None,
                "reason": f"requires_at_least_{minimum_n}_independent_units_in_category",
            })
            results[category] = summary
            continue
        selected = select_threshold(group, candidates, epsilon, delta)
        summary.update(selected)
        summary["bootstrap_stability"] = _bootstrap_stability(
            group, candidates, epsilon, delta, bootstrap_replicates, seed + index
        )
        if selected["selected_tau"] is not None:
            summary["local_decision_sensitivity"] = _sensitivity(
                group, selected["selected_tau"], tau_perturbation
            )
        else:
            summary["local_decision_sensitivity"] = None
        results[category] = summary

    all_certified = all(
        item["selection_status"] == "certified"
        and item["minimum_units_met"]
        for item in results.values()
    )
    return {
        "evaluator_version": EVALUATOR_VERSION,
        "status": "risk_certified_on_calibration_data" if all_certified else "not_certified_or_insufficient_evidence",
        "convergence_status": "not_established_missing_predeclared_stability_tolerances",
        "convergence_note": (
            "Bootstrap threshold variability and local route sensitivity are reported, "
            "but no repository-approved numeric acceptance tolerances are currently "
            "declared. Therefore this tool does not label calibration converged."
        ),
        "generalization_claim": False,
        "approved_protocol": APPROVED,
        "candidate_tau_values": candidates,
        "bootstrap_replicates": bootstrap_replicates,
        "tau_perturbation": tau_perturbation,
        "categories": results,
        "interpretation": (
            "A certified calibration threshold is not proof of out-of-family generalization. "
            "Freeze the threshold and evaluate it once on the separately locked independent cohort."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="JSON with approved_protocol, candidate_tau_values, category_list, and records")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261123)
    parser.add_argument("--tau-perturbation", type=float, default=0.01)
    args = parser.parse_args()
    if args.bootstrap_replicates < 0:
        parser.error("--bootstrap-replicates must be non-negative")
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = evaluate(
            payload, bootstrap_replicates=args.bootstrap_replicates,
            seed=args.seed, tau_perturbation=args.tau_perturbation,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                               encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": result["status"],
        "output": str(args.output),
        "categories": {
            key: {
                "selection_status": value["selection_status"],
                "selected_tau": value["selected_tau"],
                "assigned_independent_units": value["assigned_independent_units"],
            }
            for key, value in result["categories"].items()
        },
    }, indent=2))
    return 0 if result["status"] == "risk_certified_on_calibration_data" else 1


if __name__ == "__main__":
    raise SystemExit(main())
