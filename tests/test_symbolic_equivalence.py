import pytest

from hypatiax.experiments.symbolic_equivalence import adjudicate_symbolic_equivalence


def test_exact_equivalence_with_reordered_algebra():
    result = adjudicate_symbolic_equivalence(
        "def formula(a):\n    return (a*a - 1)/(a - 1)",
        "x + 1", ["x"], {"a": "x"},
    )
    assert result["status"] == "exact_symbolic_equivalent"
    assert result["symbolically_equivalent"] is True


def test_non_equivalent_formula_is_not_a_predictive_pass():
    result = adjudicate_symbolic_equivalence(
        "def formula(x):\n    return x**2", "x", ["x"]
    )
    assert result["status"] == "not_symbolically_equivalent"
    assert result["symbolically_equivalent"] is False


def test_aliases_must_be_explicit():
    result = adjudicate_symbolic_equivalence(
        "def formula(reserve_x):\n    return reserve_x",
        "x", ["reserve_x"],
    )
    assert result["status"] == "not_assessable"


def test_unsafe_or_unapproved_formula_is_never_executed():
    result = adjudicate_symbolic_equivalence(
        "def formula(x):\n    return __import__('os').system('echo unsafe')",
        "x", ["x"],
    )
    assert result["status"] == "not_assessable"


def test_missing_llm_and_answer_key_are_separate_states():
    assert adjudicate_symbolic_equivalence(None, "x", ["x"])["status"] == "no_llm_formula"
    assert adjudicate_symbolic_equivalence("def formula(x):\n    return x", None, ["x"])["status"] == "ground_truth_missing"
