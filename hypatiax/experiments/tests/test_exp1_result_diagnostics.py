"""Regression tests for the serialized Exp1 result contract."""

import copy

import pytest

from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as bench


def _record():
    return {
        "equation_id": "Impermanent loss breakeven",
        "extrapolation_intractable": True,
        "results": {
            "neural_network": {
                "success": True,
                "nn_selected_model": "log_ridge",
                "nn_abstained": True,
                "nn_edge_r2": -0.2,
                "ridge_edge_r2": 0.8,
            },
            "hybrid": {
                "success": True,
                "nn_selected_model": "log_ridge",
                "nn_abstained": True,
                "nn_edge_r2": -0.2,
                "ridge_edge_r2": 0.8,
                "blend_weights": {"llm": [1.0, 1.0], "nn": [0.0, 0.0]},
            },
        },
    }


def test_saved_result_contract_accepts_complete_diagnostics():
    bench._validate_result_records([_record()], require_il_record=True)


def test_saved_result_contract_rejects_missing_diagnostic_key():
    record = _record()
    del record["results"]["neural_network"]["ridge_edge_r2"]

    with pytest.raises(ValueError, match="missing ridge_edge_r2"):
        bench._validate_result_records([record])


def test_saved_result_contract_rejects_unknown_selected_model():
    record = _record()
    record["results"]["hybrid"]["nn_selected_model"] = "random_forest"

    with pytest.raises(ValueError, match="invalid nn_selected_model"):
        bench._validate_result_records([record])


def test_saved_result_contract_rejects_nonzero_nn_weight_after_abstention():
    record = _record()
    record["results"]["hybrid"]["blend_weights"]["nn"] = [0.0, 0.1]

    with pytest.raises(ValueError, match="all-zero NN blend weights"):
        bench._validate_result_records([record])


def test_saved_result_contract_rejects_misclassified_il_case():
    record = _record()
    record["extrapolation_intractable"] = False

    with pytest.raises(ValueError, match="extrapolation_intractable must be true"):
        bench._validate_result_records([record])


def test_legacy_resume_record_is_backfilled_without_overwriting_values():
    record = {
        "equation_id": "Impermanent loss breakeven",
        "extrapolation_intractable": False,
        "results": {
            "neural_network": {"nn_selected_model": "nn"},
            "hybrid": {"blend_weights": {"nn": [0.0], "llm": [1.0]}},
        },
    }

    normalized = bench._normalize_saved_record(copy.deepcopy(record))

    assert normalized["extrapolation_intractable"] is True
    assert normalized["results"]["neural_network"]["nn_selected_model"] == "nn"
    assert normalized["results"]["hybrid"]["blend_weights"]["nn"] == [0.0]
    for arm in ("neural_network", "hybrid"):
        for field in bench._DIAGNOSTIC_FIELDS:
            assert field in normalized["results"][arm]
