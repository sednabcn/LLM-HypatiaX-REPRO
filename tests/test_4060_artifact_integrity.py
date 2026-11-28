"""Regression tests for the committed DeFi 40/60 benchmark artifacts.

These tests inspect serialized results only. They must never import or invoke an
experiment runner, train a model, dispatch a workflow, or make an LLM request.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import pytest


RESULTS_ROOT = (
    Path(__file__).resolve().parents[1]
    / "hypatiax"
    / "data"
    / "results"
    / "comparison_results"
    / "noise-noiseless"
    / "noiseless"
)
EXPECTED_SEEDS = {42, 99, 123, 777, 2024}
EXPECTED_CASES_PER_SEED = 74
SEED_RE = re.compile(r"seed(\d+)", re.IGNORECASE)


def _seed_from_path(path: Path) -> int | None:
    match = SEED_RE.search(path.stem)
    return int(match.group(1)) if match else None


def _artifact_files(protocol: str) -> dict[int, Path]:
    """Find one committed raw artifact per expected seed, excluding checkpoints."""
    directory = RESULTS_ROOT / ("defi_pca" if protocol == "pca" else "defi")
    if not directory.is_dir():
        pytest.fail(f"Committed {protocol} artifact directory is missing: {directory}")

    if protocol == "pca":
        candidates = directory.rglob("hypatiax_defi_benchmark_pca_results_seed*.json")
    else:
        candidates = directory.rglob("hypatiax_defi_benchmark_v3*_results_seed*.json")

    by_seed: dict[int, Path] = {}
    for path in sorted(candidates):
        if "checkpoint" in path.name.lower() or path.name.startswith("_"):
            continue
        seed = _seed_from_path(path)
        if seed not in EXPECTED_SEEDS:
            continue
        # Prefer the canonical file in the protocol directory over a nested
        # duplicate/multi-seed mirror, while still accepting either layout.
        current = by_seed.get(seed)
        if current is None or (len(path.parts), str(path)) < (len(current.parts), str(current)):
            by_seed[seed] = path

    missing = EXPECTED_SEEDS - set(by_seed)
    assert not missing, f"{protocol}: missing committed seed artifacts: {sorted(missing)}"
    return by_seed


def _load_records(path: Path, expected_seed: int) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, list), f"{path}: top-level JSON must be a list"
    assert payload, f"{path}: artifact must not be empty"
    assert all(isinstance(item, dict) for item in payload), f"{path}: every case must be an object"

    for index, record in enumerate(payload):
        assert record.get("equation_id"), f"{path}[{index}]: missing equation_id"
        assert record.get("seed") == expected_seed, (
            f"{path}[{index}]: record seed {record.get('seed')!r} "
            f"does not match filename seed {expected_seed}"
        )
    return payload


def _assert_finite_or_null(value: Any, where: str) -> None:
    """JSON metrics may be null when undefined, but must not be NaN/Infinity."""
    if value is None:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        assert math.isfinite(float(value)), f"{where}: non-finite numeric value {value!r}"


@pytest.mark.parametrize("protocol", ["random", "pca"])
def test_committed_4060_artifacts_have_complete_five_seed_coverage(protocol: str):
    files = _artifact_files(protocol)
    assert set(files) == EXPECTED_SEEDS

    seen_pairs: set[tuple[str, int]] = set()
    for seed, path in files.items():
        records = _load_records(path, seed)
        assert len(records) == EXPECTED_CASES_PER_SEED, (
            f"{protocol} seed {seed}: expected {EXPECTED_CASES_PER_SEED} cases, "
            f"found {len(records)}"
        )
        for record in records:
            pair = (str(record["equation_id"]), seed)
            assert pair not in seen_pairs, f"{protocol}: duplicate equation/seed pair {pair}"
            seen_pairs.add(pair)


@pytest.mark.parametrize("protocol", ["random", "pca"])
def test_4060_case_records_preserve_auditable_structure(protocol: str):
    for seed, path in _artifact_files(protocol).items():
        records = _load_records(path, seed)
        for index, record in enumerate(records):
            where = f"{path}[{index}]"
            context = record.get("formula_context")
            assert isinstance(context, dict), f"{where}: formula_context must be an object"
            variables = context.get("variable_names")
            assert isinstance(variables, list) and variables, (
                f"{where}: variable_names must be a non-empty list"
            )
            assert len(variables) == len(set(variables)), f"{where}: duplicate variable names"

            results = record.get("results")
            assert isinstance(results, dict), f"{where}: results must be an object"
            hybrid = results.get("hybrid")
            assert isinstance(hybrid, dict), f"{where}: results.hybrid must be an object"
            assert isinstance(hybrid.get("formula"), str) and hybrid["formula"].strip(), (
                f"{where}: saved hybrid formula is missing"
            )

            split = record.get("split_protocol")
            assert isinstance(split, dict), f"{where}: split_protocol must be an object"
            split_name = str(split.get("name", "")).lower()
            assert "40" in split_name and "60" in split_name, (
                f"{where}: unexpected split protocol {split_name!r}"
            )

            audit_data = record.get("audit_data")
            assert isinstance(audit_data, dict), f"{where}: audit_data must be an object"
            arrays = {}
            for key in ("X_train", "y_train", "X_test", "y_test"):
                value = audit_data.get(key)
                assert isinstance(value, list) and value, f"{where}: {key} must be a non-empty list"
                arrays[key] = value
            assert len(arrays["X_train"]) == len(arrays["y_train"]), (
                f"{where}: X_train/y_train row counts differ"
            )
            assert len(arrays["X_test"]) == len(arrays["y_test"]), (
                f"{where}: X_test/y_test row counts differ"
            )

            for metric in (
                "llm_train_r2", "llm_test_r2", "ensemble_train_r2",
                "ensemble_test_r2", "selected_predictor_train_r2",
                "selected_predictor_test_r2", "test_r2",
            ):
                _assert_finite_or_null(hybrid.get(metric), f"{where}.results.hybrid.{metric}")


@pytest.mark.parametrize("protocol", ["random", "pca"])
def test_historical_missing_answer_keys_remain_not_assessable(protocol: str):
    """Do not infer symbolic correctness from R² or fill historical answer keys."""
    records = [
        record
        for seed, path in _artifact_files(protocol).items()
        for record in _load_records(path, seed)
    ]
    missing = [
        record for record in records
        if not (record.get("formula_context") or {}).get("ground_truth_expression")
    ]
    # This is a regression assertion for the historical master artifacts, not
    # a rule for future experiment outputs. New runs should carry answer keys.
    assert len(missing) == len(records), (
        "Historical artifact set changed: review answer-key provenance before "
        "changing this expectation; never infer ground truth from predictive scores."
    )
    assert len(records) == len(EXPECTED_SEEDS) * EXPECTED_CASES_PER_SEED
