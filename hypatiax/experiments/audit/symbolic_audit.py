"""Symbolic formula adjudication; predictive metrics are never used as a proxy."""
from __future__ import annotations

from typing import Any

from hypatiax.experiments.symbolic_equivalence import adjudicate_symbolic_equivalence


def audit_formula(
    predicted_formula: str | None,
    ground_truth: str | None,
    variable_names: list[str] | None,
    ground_truth_aliases: dict[str, str] | None = None,
    constants: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare a saved formula with its answer key using the safe AST/SymPy evaluator.

    The returned symbolic status is independent of test R² or other predictive scores.
    """
    return adjudicate_symbolic_equivalence(
        predicted_formula,
        ground_truth,
        variable_names,
        ground_truth_aliases=ground_truth_aliases,
        constants=constants,
    )
