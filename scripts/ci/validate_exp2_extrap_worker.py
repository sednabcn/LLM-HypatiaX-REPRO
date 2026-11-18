#!/usr/bin/env python3
"""Validate one REPRO worker's Exp2 Feynman extrapolation outputs.

This is an offline structural/provenance gate. It does not run experiments,
load model backends, or call any LLM API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_METHOD_COUNT = 6


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
