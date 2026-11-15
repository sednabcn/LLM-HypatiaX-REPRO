from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ci.write_protocol30_manifest import (
    build_manifest,
    load_protocol30_registry_rows,
)


def _registry_rows():
    return [
        {
            "description": f"equation {index}",
            "domain": f"domain-{(index - 1) % 11}",
            "equation_name": f"equation_{index}",
        }
        for index in range(1, 31)
    ]


def test_full_run_manifest_covers_all_equations_without_claiming_shard_aggregation(
    tmp_path: Path,
):
    (tmp_path / "protocol_core_full.json").write_text(
        json.dumps({"tests": []}), encoding="utf-8"
    )

    manifest = build_manifest(
        output_dir=tmp_path,
        shard_index=0,
        run_started_ns=0,
        indices=None,
        variant="random_8020",
        registry_rows=_registry_rows(),
        effective_temperature=0.25,
    )

    assert manifest["execution_mode"] == "single_job_full_run"
    assert manifest["n_shards"] == 1
    assert manifest["expected_equation_count"] == 30
    assert manifest["assigned_equation_indices"] == list(range(1, 31))
    assert len(manifest["equation_identities"]) == 30
    assert manifest["official_aggregate_eligible"] is False
    assert manifest["result_file"] == "protocol_core_full.json"


def test_five_shard_worker_manifest_preserves_worker_assignment(tmp_path: Path):
    (tmp_path / "protocol_core_shard.json").write_text(
        json.dumps({"tests": []}), encoding="utf-8"
    )

    manifest = build_manifest(
        output_dir=tmp_path,
        shard_index=2,
        run_started_ns=0,
        indices=[13, 14, 15, 16, 17, 18],
        variant="pca_4060",
        registry_rows=_registry_rows(),
        effective_temperature=0.25,
    )

    assert manifest["execution_mode"] == "five_shard_worker"
    assert manifest["n_shards"] == 5
    assert manifest["expected_equation_count"] == 30
    assert manifest["assigned_equation_indices"] == [13, 14, 15, 16, 17, 18]
    assert manifest["official_aggregate_eligible"] is True


def test_manifest_rejects_wrong_temperature_and_missing_outputs(tmp_path: Path):
    with pytest.raises(ValueError, match="temperature 0.25"):
        build_manifest(
            output_dir=tmp_path,
            shard_index=0,
            run_started_ns=0,
            indices=None,
            variant="random_8020",
            registry_rows=_registry_rows(),
            effective_temperature=0.5,
        )

    with pytest.raises(ValueError, match="no detailed Protocol-30 result JSON"):
        build_manifest(
            output_dir=tmp_path,
            shard_index=0,
            run_started_ns=0,
            indices=None,
            variant="random_8020",
            registry_rows=_registry_rows(),
            effective_temperature=0.25,
        )


def test_registry_enumeration_ignores_and_restores_worker_equation_ids(monkeypatch):
    worker_ids = "M.01 M.02 M.03"
    monkeypatch.setenv("SHARD_IDS", worker_ids)

    rows = load_protocol30_registry_rows()

    assert len(rows) == 30
    assert len({row["equation_name"] for row in rows}) == 30
    assert {row["domain"] for row in rows} == {
        "biology",
        "chemistry",
        "electrochemistry",
        "electromagnetism",
        "electrostatics",
        "magnetism",
        "mechanics",
        "optics",
        "probability",
        "quantum",
        "thermodynamics",
    }
    assert __import__("os").environ["SHARD_IDS"] == worker_ids
