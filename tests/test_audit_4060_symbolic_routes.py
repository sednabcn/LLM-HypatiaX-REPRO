from scripts.analysis.audit_4060_symbolic_routes import audit_record, build_audit


def test_audit_uses_saved_formula_and_preserves_route_provenance():
    record = {
        "equation_id": "toy", "seed": 7,
        "formula_context": {
            "variable_names": ["x"], "ground_truth_expression": "x * SCALE",
            "constants": {"SCALE": 2},
            "ground_truth_source": "protocol_metadata",
            "ground_truth_excluded_from_prompt": True,
        },
        "results": {"hybrid": {
            "formula": "def formula(a):\n    return a * SCALE",
            "selected_predictor_source": "nn_abstention_signed_ridge",
            "test_r2": 1.0, "llm_called": True,
            "decision": "ensemble", "route_reason": "degradation_not_calibrated",
            "structural_risk_tokens": ["division"],
            "blend_weights": {"llm": 0.7, "nn": 0.3},
            "nn_selected_model": "signed_ridge", "nn_abstained": False,
            "degradation_probe": {"source": "nn_edge_probe"},
            "ood_covariate_protocol": {"query_labels_used": False},
        }},
        "split_protocol": {"name": "random_40_60"},
        "audit_data": {"X_train": [[1.0]], "y_train": [2.0],
                       "X_test": [[2.0]], "y_test": [4.0]},
    }
    result = audit_record(record)
    assert result["symbolic_equivalence"]["symbolically_equivalent"] is True
    assert result["route"]["final_predictor_source"] == "nn_abstention_signed_ridge"
    assert result["route"]["decision"] == "ensemble"
    assert result["route"]["structural_risk_tokens"] == ["division"]
    assert result["route"]["nn_degradation_probe"]["source"] == "nn_edge_probe"
    assert result["route"]["llm_degradation_estimate"]["status"] == (
        "not_serialized_in_4060_case_record"
    )
    assert result["llm_call_status"]["called"] is True
    assert result["audit_scope"]["audit_data_shapes"]["X_train"] == {
        "rows": 1, "columns": 1
    }


def test_audit_counts_not_assessable_separately():
    report = build_audit([{"results": {"hybrid": {}}, "formula_context": {}}])
    assert report["symbolic_status_counts"] == {"no_llm_formula": 1}
