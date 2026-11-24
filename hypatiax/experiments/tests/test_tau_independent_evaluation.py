import hashlib

from scripts.validate_tau_independent_evaluation import (
    exact_bad_route_test,
    validate_evaluation,
)


CORE15 = ["core-equation"]
HASH = "a" * 64


def _record(index, *, family_id=None, bad_route=False, eligible=True, delta=0.1):
    family_id = family_id or f"eval-family-{index}"
    return {
        "equation_id": f"eval-equation-{index}",
        "canonical_equation_family_id": family_id,
        "independent_unit_id": family_id,
        "category": "finance",
        "source_ref": f"pinned-source#equation-{index}",
        "source_sha256": HASH,
        "formula_sha256": hashlib.sha256(f"formula-{index}".encode()).hexdigest(),
        "training_rows_sha256": HASH,
        "family_review_status": "adjudicated",
        "formula_equivalence_review_status": "complete",
        "core15_overlap_status": "clear",
        "historical_74_overlap_status": "clear",
        "cross_registry_overlap_status": "clear",
        "independence_status": "independent",
        "family_review_reference": f"docs/review.md#{family_id}",
        "independence_justification": "Reviewed as a distinct canonical equation family.",
        "llm_eligible": eligible,
        "delta_llm": delta if eligible else None,
        "bad_route": bad_route,
    }


def _payload(records):
    return {
        "schema_version": 1,
        "status": "evaluation_complete",
        "approved_protocol": {
            "edge_r2_floor": 0.99,
            "relative_margin": 0.0,
            "tolerated_bad_route_rate_epsilon": 0.05,
            "family_wise_error_delta": 0.05,
            "one_sided_confidence": 0.95,
            "minimum_n_if_zero_failures": 59,
        },
        "evaluation_manifest_sha256": HASH,
        "calibration_manifest_sha256": HASH,
        "historical_74_registry_sha256": HASH,
        "calibration_code_commit": "abc123",
        "evaluation_code_commit": "def456",
        "evaluator_version": "frozen-evaluator-v1",
        "calibration_family_ids": ["cal-family-1"],
        "historical_74_family_ids": ["historical-family-1"],
        "core15_exclusion_ids": CORE15,
        "category_list": ["finance"],
        "selected_tau_by_category": {"finance": 0.2},
        "records": records,
    }


def test_zero_bad_routes_need_59_accepted_independent_families():
    assert exact_bad_route_test(0, 58)["certified"] is False
    assert exact_bad_route_test(0, 59)["certified"] is True


def test_frozen_evaluation_certifies_59_accepted_zero_failure_routes():
    errors, report = validate_evaluation(
        _payload([_record(i) for i in range(59)]), CORE15
    )
    assert errors == []
    assert report["generalization_claim"] is True
    assert report["categories"]["finance"]["accepted_routes"] == 59
    assert report["categories"]["finance"]["bad_routes"] == 0


def test_abstentions_do_not_count_toward_accepted_route_precision():
    records = [_record(i) for i in range(58)]
    records.append(_record(58, eligible=False))
    errors, report = validate_evaluation(_payload(records), CORE15)
    assert errors == []
    assert report["generalization_claim"] is False
    assert report["categories"]["finance"]["accepted_routes"] == 58
    assert report["categories"]["finance"]["reason"] == "bad_route_risk_not_certified"


def test_calibration_and_historical_family_overlap_are_rejected():
    records = [_record(i) for i in range(59)]
    records[0]["canonical_equation_family_id"] = "cal-family-1"
    records[0]["independent_unit_id"] = "cal-family-1"
    records[1]["canonical_equation_family_id"] = "historical-family-1"
    records[1]["independent_unit_id"] = "historical-family-1"
    errors, report = validate_evaluation(_payload(records), CORE15)
    assert any("calibration/evaluation family overlap" in error for error in errors)
    assert any("historical-74/evaluation family overlap" in error for error in errors)
    assert report["generalization_claim"] is False


def test_core15_equation_overlap_is_rejected():
    records = [_record(i) for i in range(59)]
    records[0]["equation_id"] = "core-equation"
    errors, _ = validate_evaluation(_payload(records), CORE15)
    assert any("Core-15/evaluation overlap" in error for error in errors)


def test_one_bad_route_among_59_is_not_certified():
    assert exact_bad_route_test(1, 59)["certified"] is False



def test_duplicate_formula_hashes_are_rejected_even_with_distinct_ids():
    records = [_record(i) for i in range(59)]
    records[1]["formula_sha256"] = records[0]["formula_sha256"]
    errors, report = validate_evaluation(_payload(records), CORE15)
    assert any("duplicate evaluation formula_sha256" in error for error in errors)
    assert report["generalization_claim"] is False
