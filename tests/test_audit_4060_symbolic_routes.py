from scripts.analysis.audit_4060_symbolic_routes import audit_record, build_audit


def test_audit_keeps_llm_formula_separate_from_selected_predictor():
    record = {
        "equation_id": "toy", "seed": 7,
        "formula_context": {
            "variable_names": ["x"], "ground_truth_expression": "x + 1",
            "ground_truth_source": "protocol_metadata",
            "ground_truth_excluded_from_prompt": True,
        },
        "results": {"hybrid": {
            "formula": "def formula(a):\n    return a + 1",
            "selected_predictor_source": "nn_abstention_signed_ridge",
            "test_r2": 1.0, "llm_called": True,
        }},
        "split_protocol": {"name": "random_40_60"},
        "audit_data": {"X_train": [[1.0]], "X_test": [[2.0]]},
    }
    result = audit_record(record)
    assert result["symbolic_equivalence"]["symbolically_equivalent"] is True
    assert result["route"]["final_predictor_source"] == "nn_abstention_signed_ridge"
    assert result["audit_scope"]["formula_compared"].startswith("saved hybrid.formula")


def test_audit_counts_not_assessable_separately():
    report = build_audit([{"results": {"hybrid": {}}, "formula_context": {}}])
    assert report["symbolic_status_counts"] == {"no_llm_formula": 1}
