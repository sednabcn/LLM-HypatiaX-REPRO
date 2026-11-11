from pathlib import Path

from scripts.validate_tau_calibration_manifest import (
    extract_core15_ids,
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
    assert any("non-independent repeated unit" in e for e in errors)


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
