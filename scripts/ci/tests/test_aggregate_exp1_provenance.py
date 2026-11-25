import hashlib
import json
from pathlib import Path

import pytest

from scripts.ci.aggregate_exp1_provenance import EXPECTED_SEEDS, aggregate


def _fixture(root: Path, *, missing_id_seed=None):
    ids = ["Equation A", "Equation B"]
    for seed in EXPECTED_SEEDS:
        records = []
        for eq in ids:
            if seed == missing_id_seed and eq == "Equation B":
                continue
            nn = {"success": True, "test_r2": 0.8, "time_s": 0.1}
            hy = {
                "success": True, "test_r2": 0.9, "time_s": 0.2,
                "decision": "ensemble", "llm_input_tokens": 10,
                "llm_output_tokens": 4, "nn_component_time_s": 0.1,
                "hybrid_component_time_s": 0.1, "llm_api_request_time_s": 0.05,
            }
            if eq == "Equation B":
                nn["test_r2"] = None
                hy["test_r2"] = None
            records.append({
                "equation_id": eq, "seed": seed, "difficulty": "medium",
                "extrapolation_intractable": eq == "Equation B",
                "results": {"neural_network": nn, "hybrid": hy},
            })
        result = root / f"result_seed{seed}.json"
        result.write_text(json.dumps(records), encoding="utf-8")
        manifest = {
            "seed": seed, "experiment_id": "exp1-provenance", "status": "passed",
            "expected_case_count": len(records), "observed_case_count": len(records),
            "result_file": result.name,
            "result_sha256": hashlib.sha256(result.read_bytes()).hexdigest(),
            "script_sha256": "script", "protocol_config_sha256": "protocol",
            "repro_config_sha256": "repro",
        }
        (root / f"exp1-provenance_seed{seed}_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )


def test_aggregate_joins_equation_ids_and_keeps_repeated_seeds(tmp_path):
    _fixture(tmp_path)
    summary, rows = aggregate(tmp_path)

    assert summary["unique_equation_count"] == 2
    assert summary["seed_equation_record_count"] == 10
    assert len(rows) == 10
    assert summary["per_equation"]["Equation A"]["paired_hybrid_minus_nn_test_r2"]["mean"] == pytest.approx(0.1)
    assert summary["per_equation"]["Equation A"]["n_seed_records"] == 5
    assert "not 370 independent" in summary["interpretation"]


def test_undefined_and_intractable_cases_are_not_dropped(tmp_path):
    _fixture(tmp_path)
    summary, rows = aggregate(tmp_path)

    eq_b = summary["per_equation"]["Equation B"]
    assert eq_b["extrapolation_intractable"] is True
    assert eq_b["neural_network_test_r2"]["n_finite"] == 0
    assert eq_b["hybrid_test_r2"]["n_finite"] == 0
    assert sum(row["case_status"] == "intractable" for row in rows) == 5


def test_aggregate_rejects_cross_seed_equation_id_mismatch(tmp_path):
    _fixture(tmp_path, missing_id_seed=99)
    with pytest.raises(ValueError, match="expected 74/74|expected 74 records|equation IDs differ"):
        aggregate(tmp_path)
