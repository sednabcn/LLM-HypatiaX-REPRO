"""Offline tests for the deterministic exp1c Protocol-30 projection."""

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "scripts/ci/project_protocol30_exp1c_view.py"
SPEC = importlib.util.spec_from_file_location("project_protocol30_exp1c_view", HELPER)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


METHODS = [
    "PureLLMBaseline",
    "ImprovedNN",
    "EnhancedHybridDeFi",
    "HybridLLMNN",
    "SymbolicEngineWithLLM",
    "HybridDiscoverySystem",
]


def _aggregate():
    return {
        "timestamp": "2026-11-21T00:00:00Z",
        "protocol": {
            "mode": "noiseless_pca",
            "noise_injected": False,
            "noise_level": 0.0,
            "n_samples": 200,
        },
        "methods": METHODS,
        "total_tests": 30,
        "protocol30_aggregate": {
            "variant": "pca_4060",
            "shard_count": 5,
            "equation_count": 30,
            "method_failure_counts": {name: 0 for name in METHODS},
        },
        "tests": [
            {
                "equation_index": i,
                "domain": "mechanics",
                "description": f"equation {i}",
                "results": {
                    name: {"success": True, "r2": float(i)}
                    for name in METHODS
                },
            }
            for i in range(1, 31)
        ],
    }


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_projection_keeps_only_methods_2_and_3_and_preserves_source(tmp_path):
    source = tmp_path / "protocol30_pca_4060_aggregate.json"
    output = tmp_path / "protocol30_pca_4060_exp1c_view.json"
    _write(source, _aggregate())
    original = source.read_bytes()

    result = module.project_protocol30_exp1c(source, output)
    view = json.loads(output.read_text(encoding="utf-8"))

    assert source.read_bytes() == original
    assert result["method_ids"] == [2, 3]
    assert result["method_names"] == ["ImprovedNN", "EnhancedHybridDeFi"]
    assert view["total_tests"] == 30
    assert len(view["tests"]) == 30
    assert all(
        list(record["results"]) == ["ImprovedNN", "EnhancedHybridDeFi"]
        for record in view["tests"]
    )
    assert view["projection_only"] is True
    assert view["execution_performed"] is False
    assert view["source_sha256"]


def test_projection_rejects_non_pca_or_wrong_protocol_variant(tmp_path):
    source = tmp_path / "aggregate.json"
    output = tmp_path / "view.json"
    payload = _aggregate()
    payload["protocol30_aggregate"]["variant"] = "random_8020"
    _write(source, payload)

    with pytest.raises(ValueError, match="PCA 40/60"):
        module.project_protocol30_exp1c(source, output)


def test_projection_rejects_wrong_method_registry_order(tmp_path):
    source = tmp_path / "aggregate.json"
    output = tmp_path / "view.json"
    payload = _aggregate()
    payload["methods"][1] = "DifferentNN"
    _write(source, payload)

    with pytest.raises(ValueError, match="method registry IDs"):
        module.project_protocol30_exp1c(source, output)


def test_projection_rejects_missing_method_result(tmp_path):
    source = tmp_path / "aggregate.json"
    output = tmp_path / "view.json"
    payload = _aggregate()
    del payload["tests"][0]["results"]["EnhancedHybridDeFi"]
    _write(source, payload)

    with pytest.raises(ValueError, match="does not preserve all six"):
        module.project_protocol30_exp1c(source, output)


def test_projection_never_overwrites_its_source(tmp_path):
    source = tmp_path / "aggregate.json"
    _write(source, _aggregate())

    with pytest.raises(ValueError, match="must not overwrite"):
        module.project_protocol30_exp1c(source, source)


def test_protocol30_aggregate_stage_emits_the_exp1c_view():
    runner = (ROOT / "run_all.sh").read_text()
    start = runner.index('run exp2_protocol30_pca_4060_aggregate "')
    end = runner.find("\nrun ", start + 1)
    block = runner[start:end if end >= 0 else len(runner)]

    assert "project_protocol30_exp1c_view.py" in block
    assert "protocol30_pca_4060_aggregate.json" in block
    assert "protocol30_pca_4060_exp1c_view.json" in block
