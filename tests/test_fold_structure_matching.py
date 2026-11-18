"""Regression source for conservative fold-structure recurrence matching."""
import pytest

from hypatiax.tools.symbolic.structural_matching import (
    canonicalize_symbolic_structure,
    match_fold_discovered_structures,
)


def test_numeric_coefficients_are_abstracted_but_exponents_remain_structural():
    linear_a = canonicalize_symbolic_structure("2.0*x0 + 1.5", ["x0"])
    linear_b = canonicalize_symbolic_structure("7.25*x0 + 9.0", ["x0"])
    quadratic = canonicalize_symbolic_structure("7.25*x0**2 + 9.0", ["x0"])

    assert linear_a == linear_b
    assert linear_a != quadratic


def test_equivalent_arithmetic_forms_share_conservative_signature():
    expanded = canonicalize_symbolic_structure("x0 + x0", ["x0"])
    scaled = canonicalize_symbolic_structure("3.0*x0", ["x0"])
    assert expanded == scaled


def test_undeclared_variables_fail_closed():
    with pytest.raises(ValueError, match="Undeclared variable"):
        canonicalize_symbolic_structure("x0 + hidden", ["x0"])


def test_recurrence_groups_only_matching_structures_and_scores_matching_folds():
    searches = [
        {"repeat": 0, "fold": 0, "expression": "2.0*x0 + 1.0"},
        {"repeat": 0, "fold": 1, "expression": "8.0*x0 + 4.0"},
        {"repeat": 0, "fold": 2, "expression": "x0**2"},
    ]
    metrics = [
        {"repeat": 0, "fold": 0, "normalized_rmse": 0.2, "rmse": 1.0, "validation_size": 5},
        {"repeat": 0, "fold": 1, "normalized_rmse": 0.4, "rmse": 2.0, "validation_size": 5},
        {"repeat": 0, "fold": 2, "normalized_rmse": 0.1, "rmse": 0.5, "validation_size": 5},
    ]

    result = match_fold_discovered_structures(
        searches, metrics, ["x0"],
        minimum_recurrence=2,
        minimum_recurrence_fraction=0.5,
        total_fold_count=3,
    )

    assert result["status"] == "matched_structures"
    eligible = [item for item in result["structures"] if item["eligible"]]
    assert len(eligible) == 1
    assert eligible[0]["recurrence_count"] == 2
    assert eligible[0]["recurrence_fraction"] == pytest.approx(2 / 3)
    assert eligible[0]["mean_normalized_rmse"] == pytest.approx(0.3)
    assert eligible[0]["score_fold_count"] == 2
    assert result["equivalence_claim"] is False
    assert result["far_test_data_used"] is False


def test_failed_fold_counts_against_recurrence_fraction():
    searches = [
        {"repeat": 0, "fold": 0, "expression": "x0"},
        {"repeat": 0, "fold": 1, "expression": "2.0*x0"},
    ]
    metrics = [
        {"repeat": 0, "fold": 0, "normalized_rmse": 0.2},
        {"repeat": 0, "fold": 1, "normalized_rmse": 0.3},
    ]
    result = match_fold_discovered_structures(
        searches, metrics, ["x0"],
        minimum_recurrence=2,
        minimum_recurrence_fraction=0.75,
        total_fold_count=3,
    )
    assert result["status"] == "NO_RECURRENT_CANDIDATE"
    assert result["structures"][0]["recurrence_fraction"] == pytest.approx(2 / 3)
    assert result["structures"][0]["eligible"] is False
