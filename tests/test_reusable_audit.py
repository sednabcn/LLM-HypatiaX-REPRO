import math

from hypatiax.experiments.audit import (
    audit_formula,
    compare_callables,
    validate_formula_metadata,
)


def test_public_symbolic_api_reports_exact_equivalence():
    result = audit_formula(
        "def formula(x):\n    return x*x + 2*x + 1",
        "(x + 1)**2",
        ["x"],
    )
    assert result["status"] == "exact_symbolic_equivalent"
    assert result["symbolically_equivalent"] is True


def test_public_symbolic_api_keeps_missing_answer_key_distinct():
    result = audit_formula("def formula(x):\n    return x", None, ["x"])
    assert result["status"] == "ground_truth_missing"
    assert result["symbolically_equivalent"] is None


def test_metadata_validation_rejects_duplicate_variables():
    result = validate_formula_metadata("def formula(x): return x", ["x", "x"])
    assert result["valid"] is False
    assert "unique" in result["errors"][0]


def test_metadata_validation_rejects_non_finite_constants():
    result = validate_formula_metadata("formula", ["x"], {"K": math.inf})
    assert result["valid"] is False


def test_numerical_audit_compares_only_explicit_trusted_callables():
    result = compare_callables(lambda x: x * x, lambda x: x**2, [(0,), (2,), (3,)])
    assert result["status"] == "numerically_agree"
    assert result["checked"] == 3


def test_numerical_audit_reports_disagreement():
    result = compare_callables(lambda x: x + 1, lambda x: x, [(1,), (2,)])
    assert result["status"] == "numerically_disagree"
    assert len(result["failures"]) == 2


def test_numerical_audit_does_not_accept_formula_strings():
    result = compare_callables("lambda x: x", lambda x: x, [(1,)])
    assert result["status"] == "not_assessable"


def test_numerical_audit_requires_nonempty_points():
    result = compare_callables(lambda x: x, lambda x: x, [])
    assert result["status"] == "not_assessable"
