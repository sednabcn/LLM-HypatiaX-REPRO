"""Regression tests for the DeFi-74 result completeness contract."""

import pytest

from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as benchmark


def _record(case_id):
    diagnostics = {
        "nn_selected_model": None,
        "nn_abstained": False,
        "nn_edge_r2": None,
        "ridge_edge_r2": None,
    }
    return {
        "equation_id": case_id,
        "extrapolation_intractable": (
            "impermanent loss breakeven" in case_id.lower()
        ),
        "results": {
            "neural_network": {**diagnostics, "success": False},
            "hybrid": {**diagnostics, "success": False},
        },
    }


def _complete_records():
    return [_record(case["name"]) for case in benchmark._get_test_cases()]


def test_defi74_catalogue_has_74_cases_and_one_intractable():
    cases = benchmark._get_test_cases()
    assert len(cases) == 74
    assert sum(benchmark._is_intractable_case(case) for case in cases) == 1
    assert benchmark._STANDARD_TOTAL == 73


def test_complete_defi74_result_set_passes():
    records = _complete_records()
    benchmark._validate_result_records(
        records, require_il_record=True, require_complete=True
    )


def test_final_validation_rejects_missing_case():
    records = _complete_records()
    records.pop()
    with pytest.raises(ValueError, match="incomplete DeFi-74 result"):
        benchmark._validate_result_records(records, require_complete=True)


def test_final_validation_rejects_duplicate_case_id():
    records = _complete_records()
    records[-1] = dict(records[0])
    with pytest.raises(ValueError, match="duplicate case IDs"):
        benchmark._validate_result_records(records, require_complete=True)


def test_validation_rejects_unexpected_case_even_for_checkpoint():
    records = [_record("not-a-DeFi-74-case")]
    with pytest.raises(ValueError, match="unexpected case ID"):
        benchmark._validate_result_records(records, require_complete=False)


def test_partial_checkpoint_is_allowed_but_not_final_output():
    records = _complete_records()[:3]
    benchmark._validate_result_records(records, require_complete=False)
    with pytest.raises(ValueError, match="incomplete DeFi-74 result"):
        benchmark._validate_result_records(records, require_complete=True)


def test_validation_rejects_wrong_intractability_classification():
    records = _complete_records()
    il_record = next(
        record for record in records
        if "impermanent loss breakeven" in record["equation_id"].lower()
    )
    il_record["extrapolation_intractable"] = False
    with pytest.raises(ValueError, match="extrapolation_intractable must be True"):
        benchmark._validate_result_records(records, require_complete=True)


def test_filtered_portfolio_scope_passes_without_full_catalogue_or_il_record():
    portfolio_cases = [
        case for case in benchmark._get_test_cases()
        if "portfolio" in case["name"].lower()
    ]
    assert portfolio_cases
    assert not any(
        "impermanent loss breakeven" in case["name"].lower()
        for case in portfolio_cases
    )
    records = [_record(case["name"]) for case in portfolio_cases]

    benchmark._validate_result_records(
        records,
        require_il_record=False,
        require_complete=True,
        expected_cases=portfolio_cases,
    )


def test_filtered_scope_rejects_missing_selected_case():
    portfolio_cases = [
        case for case in benchmark._get_test_cases()
        if "portfolio" in case["name"].lower()
    ]
    records = [_record(case["name"]) for case in portfolio_cases[:-1]]

    with pytest.raises(ValueError, match="incomplete filtered benchmark result"):
        benchmark._validate_result_records(
            records,
            require_complete=True,
            expected_cases=portfolio_cases,
        )


def test_filtered_scope_rejects_case_outside_selected_filter():
    portfolio_cases = [
        case for case in benchmark._get_test_cases()
        if "portfolio" in case["name"].lower()
    ]
    outside_case = next(
        case for case in benchmark._get_test_cases()
        if "portfolio" not in case["name"].lower()
    )
    records = [_record(case["name"]) for case in portfolio_cases]
    records[-1] = _record(outside_case["name"])

    with pytest.raises(ValueError, match="unexpected case ID"):
        benchmark._validate_result_records(
            records,
            require_complete=True,
            expected_cases=portfolio_cases,
        )

