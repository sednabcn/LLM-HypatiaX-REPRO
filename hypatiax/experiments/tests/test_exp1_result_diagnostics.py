"""Regression tests for the serialized Exp1 result contract."""

import copy
import json

import pytest

from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as bench
from hypatiax.core.base_pure_llm import baseline_pure_llm_defi_discovery as pure_module


def _record():
    return {
        "equation_id": "Impermanent loss breakeven fee rate",
        "extrapolation_intractable": True,
        "results": {
            "pure_llm": {
                "time_s": 0.5, "generation_time_s": 0.4,
                "evaluation_time_s": 0.1, "llm_called": True,
                "model": "claude-sonnet-4-6",
                "input_tokens": 100, "output_tokens": 50,
            },
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

    with pytest.raises(ValueError, match="extrapolation_intractable must be True"):
        bench._validate_result_records([record])


def test_legacy_resume_record_is_backfilled_without_overwriting_values():
    record = {
        "equation_id": "Impermanent loss breakeven fee rate",
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
    assert "pure_llm" not in normalized["results"]



def test_legacy_two_arm_checkpoint_is_discarded_for_three_arm_protocol(tmp_path, monkeypatch):
    checkpoint = tmp_path / "legacy.json"
    checkpoint.write_text(json.dumps([_record_without_pure_llm()]))
    monkeypatch.setattr(bench, "CHECKPOINT_FILE", checkpoint)

    records, completed = bench._load_checkpoint()

    assert records == []
    assert completed == 0


def _record_without_pure_llm():
    record = _record()
    del record["results"]["pure_llm"]
    return record



def test_pure_llm_arm_uses_same_split_model_and_persists_usage(monkeypatch):
    import numpy as np

    observed = {}

    class FakePureLLM:
        def __init__(self, model):
            observed["model"] = model

        def generate_formula(self, description, domain, var_names, metadata):
            observed["generation_args"] = (description, domain, list(var_names))
            return {
                "llm_called": True,
                "llm_attempted": True,
                "formula_present": True,
                "model": bench.LLM_MODEL,
                "model_source": "explicit",
                "prompt_sha256": "abc",
                "temperature_requested": 0.25,
                "temperature_sent": True,
                "usage": {"in": 123, "out": 45},
                "python_code": "def formula(x): return x",
            }

        def test_formula_accuracy(self, formula, X, y, var_names, verbose=False):
            observed.setdefault("scored_shapes", []).append((X.shape, y.shape))
            return {"success": True, "r2": 0.99 if len(y) == 4 else 0.98}

    monkeypatch.setattr(pure_module, "PureLLMBaseline", FakePureLLM)
    X_train = np.ones((4, 1))
    y_train = np.ones(4)
    X_test = np.ones((2, 1))
    y_test = np.ones(2)

    result = bench._run_pure_llm_arm(
        "description", "amm", ["x"], {"constants": {}},
        X_train, y_train, X_test, y_test,
    )

    assert observed["model"] == bench.LLM_MODEL
    assert observed["scored_shapes"] == [((4, 1), (4,)), ((2, 1), (2,))]
    assert result["train_r2"] == 0.99
    assert result["test_r2"] == 0.98
    assert result["input_tokens"] == 123
    assert result["output_tokens"] == 45
    assert result["llm_called"] is True
    assert result["temperature_sent"] is True


def test_pure_llm_client_uses_hybrid_timeout_and_no_sdk_retries(monkeypatch):
    observed = {}

    class FakeAnthropic:
        def __init__(self, **kwargs):
            observed.update(kwargs)

    monkeypatch.setattr(pure_module, "Anthropic", FakeAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("LLM_METHOD_TIMEOUT", "37")

    pure_module.PureLLMBaseline(model=bench.LLM_MODEL)

    assert observed["timeout"] == 37.0
    assert observed["max_retries"] == 0
