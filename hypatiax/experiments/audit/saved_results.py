"""Post-hoc symbolic audits for persisted experiment result files.

This module reads saved JSON records only. It does not launch experiments, train
models, call an LLM, or execute formula source strings.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .formula_validation import validate_formula_metadata
from .symbolic_audit import audit_formula


def audit_saved_records(
    records: Iterable[dict[str, Any]],
    *,
    experiment_id: str,
    split_protocol: str,
    source_files: list[str] | None = None,
) -> dict[str, Any]:
    """Audit saved formula metadata and symbolic identity without rerunning work."""
    cases: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("every saved result record must be a JSON object")
        context = record.get("formula_context") or {}
        results = record.get("results") or {}
        hybrid = results.get("hybrid") or {}
        formula = hybrid.get("formula")
        variables = context.get("variable_names")
        constants = context.get("constants")
        aliases = context.get("ground_truth_aliases")

        pair = (record.get("seed"), record.get("equation_id"))
        if pair[0] is not None and pair[1] is not None:
            if pair in seen:
                raise ValueError(f"duplicate seed/equation record: {pair!r}")
            seen.add(pair)

        metadata = validate_formula_metadata(
            formula,
            variables,
            constants if isinstance(constants, dict) else None,
        )
        symbolic = audit_formula(
            formula,
            context.get("ground_truth_expression"),
            variables,
            ground_truth_aliases=aliases if isinstance(aliases, dict) else None,
            constants=constants if isinstance(constants, dict) else None,
        )
        cases.append({
            "equation_id": record.get("equation_id"),
            "seed": record.get("seed"),
            "formula_metadata": metadata,
            "symbolic_audit": symbolic,
            "ground_truth_source": context.get("ground_truth_source"),
            "ground_truth_excluded_from_prompt": context.get(
                "ground_truth_excluded_from_prompt"
            ),
            "split_protocol": record.get("split_protocol"),
            "source_file": record.get("_audit_source_file"),
        })

    statuses = Counter(case["symbolic_audit"]["status"] for case in cases)
    metadata_statuses = Counter(
        case["formula_metadata"]["status"] for case in cases
    )
    return {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "split_protocol": split_protocol,
        "case_count": len(cases),
        "source_files": source_files or [],
        "coverage": {
            "formula_present": sum(
                case["formula_metadata"]["valid"] for case in cases
            ),
            "ground_truth_present": sum(
                case["symbolic_audit"]["status"] != "ground_truth_missing"
                for case in cases
            ),
            "variable_schema_present": sum(
                case["formula_metadata"]["status"] == "valid_metadata"
                for case in cases
            ),
            "ground_truth_excluded_from_prompt": sum(
                case["ground_truth_excluded_from_prompt"] is True
                for case in cases
            ),
        },
        "formula_metadata_status_counts": dict(metadata_statuses),
        "symbolic_status_counts": dict(statuses),
        "cases": cases,
        "interpretation": (
            "Symbolic status is computed from saved formula and answer-key metadata. "
            "Predictive R2 is not used as evidence of symbolic equivalence. "
            "Not-assessable cases remain distinct from equivalent and non-equivalent."
        ),
    }


def audit_saved_files(
    files: Iterable[Path],
    *,
    experiment_id: str,
    split_protocol: str,
) -> dict[str, Any]:
    """Load saved JSON result files and audit their records in place."""
    records: list[dict[str, Any]] = []
    source_files: list[str] = []
    for path in files:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"{path} must contain a JSON list of result records")
        source_files.append(str(path))
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError(f"{path} contains a non-object result record")
            record = dict(item)
            record["_audit_source_file"] = path.name
            records.append(record)
    return audit_saved_records(
        records,
        experiment_id=experiment_id,
        split_protocol=split_protocol,
        source_files=source_files,
    )
