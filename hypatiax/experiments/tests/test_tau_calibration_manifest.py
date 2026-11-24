from pathlib import Path

from scripts.validate_tau_calibration_manifest import (
    extract_core15_ids,
    minimum_n_zero_failures,
    validate_manifest,
)


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "hypatiax/experiments/benchmarks/exp1_ablation.py"


def _manifest():
    import json
    return json.loads(
        (ROOT / "config/tau_calibration_manifest.json").read_text(encoding="utf-8")
    )


def test_core15_catalogue_extraction_is_exact_and_stable():
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    assert len(ids) == 15
    assert ids[0] == "Arrhenius"
    assert ids[-1] == "Portfolio Std Dev"


def test_draft_manifest_records_approved_values_but_is_not_ready():
    manifest = _manifest()
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    assert validate_manifest(manifest, ids) == []
    errors = validate_manifest(manifest, ids, require_ready=True)
    assert any("status must be ready_for_calibration" in e for e in errors)
    assert any("predeclared calibration equation" in e for e in errors)


def test_core15_equation_cannot_enter_calibration_set():
    manifest = _manifest()
    manifest["calibration_equations"] = [{
        "equation_id": "Arrhenius",
        "category": "chemistry",
        "independent_unit_id": "family-a",
        "provenance": "forbidden test fixture",
        "uses_training_data_only": True,
    }]
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids)
    assert any("Core-15 leakage: Arrhenius" in e for e in errors)


def test_duplicate_independence_unit_is_rejected_within_category():
    manifest = _manifest()
    base = {
        "category": "chemistry",
        "independent_unit_id": "same-family",
        "provenance": "predeclared source registry",
        "uses_training_data_only": True,
    }
    manifest["calibration_equations"] = [
        dict(base, equation_id="cal-chem-001"),
        dict(base, equation_id="cal-chem-002"),
    ]
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids)
    assert any("independent_unit_id" in e and "reused" in e for e in errors)


def test_heldout_fields_are_rejected():
    manifest = _manifest()
    manifest["calibration_equations"] = [{
        "equation_id": "calibration-only-001",
        "category": "chemistry",
        "independent_unit_id": "family-001",
        "provenance": "predeclared source registry",
        "uses_training_data_only": True,
        "heldout_scores": [0.99],
    }]
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids)
    assert any("forbidden fields" in e for e in errors)


def test_independence_unit_cannot_be_reused_across_categories():
    manifest = _manifest()
    base = {
        "independent_unit_id": "shared-family",
        "provenance": "predeclared source registry",
        "uses_training_data_only": True,
    }
    manifest["calibration_equations"] = [
        dict(base, equation_id="cal-chem-001", category="chemistry"),
        dict(base, equation_id="cal-bio-001", category="biology"),
    ]
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids)
    assert any("reused" in e and "entire calibration manifest" in e for e in errors)


def test_readiness_requires_hash_pinned_data_code_and_evaluator():
    manifest = _manifest()
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids, require_ready=True)
    assert any("calibration_data_manifest_sha256" in e for e in errors)
    assert any("calibration_code_commit" in e for e in errors)
    assert any("evaluator_version" in e for e in errors)


def test_fixed_sequence_zero_failure_sample_sizes_follow_epsilon_delta():
    assert minimum_n_zero_failures(0.05, 0.05) == 59
    assert [minimum_n_zero_failures(e, 0.05) for e in (0.05, 0.10, 0.15, 0.20, 0.25)] == [59, 29, 19, 14, 11]


def test_candidate_grid_must_be_strictest_to_laxest():
    manifest = _manifest()
    manifest["candidate_tau_values"] = [0.3, 0.1, 0.2]
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids)
    assert any("strictest-to-laxest" in e for e in errors)


def test_ready_manifest_rejects_unreviewed_family_even_with_unique_ids():
    manifest = _manifest()
    manifest.update({
        "status": "ready_for_calibration",
        "candidate_tau_values": [0.05],
        "category_list": ["chemistry"],
        "category_definition": "One predeclared mathematical stratum.",
        "independence_justification": "Family-level review protocol.",
        "frozen_edge_definition": "Frozen edge construction and scoring protocol.",
        "calibration_data_manifest_sha256": "a" * 64,
        "calibration_code_commit": "abc123",
        "evaluator_version": "tau-convergence-evaluator-v1",
    })
    manifest["calibration_equations"] = [{
        "equation_id": "candidate-001",
        "category": "chemistry",
        "independent_unit_id": "invented-unique-id",
        "canonical_equation_family_id": "invented-unique-id",
        "provenance": "pinned source",
        "source_ref": "source#candidate-001",
        "source_sha256": "b" * 64,
        "formula_sha256": "c" * 64,
        "training_rows_sha256": "d" * 64,
        "uses_training_data_only": True,
        "family_review_status": "unreviewed",
        "formula_equivalence_review_status": "not_checked",
        "core15_overlap_status": "not_checked",
        "historical_74_overlap_status": "not_checked",
        "cross_registry_overlap_status": "not_checked",
        "independence_status": "not_adjudicated",
    }]
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids, require_ready=True)
    assert any("family_review_status must be 'adjudicated'" in e for e in errors)
    assert any("formula_equivalence_review_status must be 'complete'" in e for e in errors)
    assert any("core15_overlap_status must be 'clear'" in e for e in errors)
    assert any("historical_74_overlap_status must be 'clear'" in e for e in errors)
    assert any("cross_registry_overlap_status must be 'clear'" in e for e in errors)
    assert any("independence_status must be 'independent'" in e for e in errors)
    assert any("family_review_reference" in e for e in errors)
    assert any("independence_justification" in e for e in errors)


def test_ready_manifest_requires_family_id_to_match_independent_unit():
    manifest = _manifest()
    manifest.update({
        "status": "ready_for_calibration",
        "candidate_tau_values": [0.05],
        "category_list": ["chemistry"],
        "category_definition": "One predeclared mathematical stratum.",
        "independence_justification": "Family-level review protocol.",
        "frozen_edge_definition": "Frozen edge construction and scoring protocol.",
        "calibration_data_manifest_sha256": "a" * 64,
        "calibration_code_commit": "abc123",
        "evaluator_version": "tau-convergence-evaluator-v1",
    })
    manifest["calibration_equations"] = [{
        "equation_id": "candidate-001",
        "category": "chemistry",
        "independent_unit_id": "family-001",
        "canonical_equation_family_id": "family-002",
        "provenance": "pinned source",
        "source_ref": "source#candidate-001",
        "source_sha256": "b" * 64,
        "formula_sha256": "c" * 64,
        "training_rows_sha256": "d" * 64,
        "uses_training_data_only": True,
        "family_review_status": "adjudicated",
        "formula_equivalence_review_status": "complete",
        "core15_overlap_status": "clear",
        "historical_74_overlap_status": "clear",
        "cross_registry_overlap_status": "clear",
        "independence_status": "independent",
        "family_review_reference": "docs/review.md#family-001",
        "independence_justification": "Distinct reviewed equation family.",
    }]
    ids = extract_core15_ids(SOURCE.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, ids, require_ready=True)
    assert any("must equal the adjudicated canonical_equation_family_id" in e for e in errors)
