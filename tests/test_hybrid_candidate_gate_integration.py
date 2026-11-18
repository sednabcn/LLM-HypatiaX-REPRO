"""Integration tests: declared scientific gates must control retry eligibility."""
from types import SimpleNamespace

import pytest

from hypatiax.tools.symbolic.discovery_contracts import ConstraintSpec, DiscoveryProblem
from hypatiax.tools.symbolic.hybrid_system_v50_2 import HybridDiscoverySystem
from hypatiax.tools.symbolic.discovery_validation import CandidateValidator


class _FakeSymbolicEngine:
    def __init__(self, expression):
        self.config = SimpleNamespace(
            use_transcendental_compositions=False,
            unary_operators=[],
        )
        self.llm_engine = None
        self.expression = expression

    def discover(self, *args, **kwargs):
        return {
            "expression": self.expression,
            "r2_score": 0.999999,
            "llm_mode": "none",
        }


def _system(expression, problem):
    system = HybridDiscoverySystem.__new__(HybridDiscoverySystem)
    system.symbolic_engine = _FakeSymbolicEngine(expression)
    system.max_retries = 1
    system._pysr_deterministic = False
    system.enable_physics_fallback = False
    system.physics_fallback_threshold = 0.85
    system._active_discovery_problem = problem
    system._candidate_validator = CandidateValidator()
    system.stats = {
        "symbolic_attempts": 0,
        "llm_skipped": 0,
        "llm_guided": 0,
        "symbolic_successes": 0,
        "symbolic_failures": 0,
        "physics_used": 0,
        "physics_successes": 0,
    }
    system._check_expression_quality = lambda expression, r2: {
        "is_overfit": False,
        "complexity": 3,
        "warnings": [],
    }
    system._detect_rational_pattern = lambda X, y: False
    return system


def test_retry_selector_accepts_candidate_that_passes_declared_gate():
    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2, "maximum": 2}},
        constraints=(
            ConstraintSpec(
                constraint_id="energy-nonnegative",
                kind="nonnegative_output",
                severity="hard",
            ),
        ),
    )
    system = _system("x**2", problem)

    result = system._discover_with_retry(
        X=__import__("numpy").array([[-1.0], [0.0], [1.0]]),
        y=__import__("numpy").array([1.0, 0.0, 1.0]),
        variable_names=["x"],
        variable_descriptions={"x": "position"},
        variable_units={},
    )

    assert result["candidate_validation_status"] == "eligible"
    assert result["candidate_validation"]["eligible"] is True


def test_retry_selector_never_returns_candidate_failing_hard_gate():
    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2, "maximum": 2}},
        constraints=(
            ConstraintSpec(
                constraint_id="energy-strictly-positive",
                kind="positive_output",
                severity="hard",
            ),
        ),
    )
    system = _system("x**2", problem)

    with pytest.raises(ValueError, match="All 1 discovery attempts failed"):
        system._discover_with_retry(
            X=__import__("numpy").array([[-1.0], [0.0], [1.0]]),
            y=__import__("numpy").array([1.0, 0.0, 1.0]),
            variable_names=["x"],
            variable_descriptions={"x": "position"},
            variable_units={},
        )



def test_training_only_report_selects_candidate_from_candidate_specific_fold_evidence():
    import numpy as np

    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2, "maximum": 2}},
        constraints=(
            ConstraintSpec(
                constraint_id="energy-nonnegative",
                kind="nonnegative_output",
                severity="hard",
            ),
        ),
    )
    system = _system("x**2", problem)
    X = np.linspace(-2.0, 2.0, 20).reshape(-1, 1)
    y = np.square(X[:, 0])
    system._active_training_validation_settings = {
        "n_splits": 2,
        "validation_fraction": 0.2,
        "minimum_valid_folds": 2,
    }
    system._active_training_validation_seed = 42
    system._discover_X_orig = X
    system._discover_y_orig = y

    result = system._discover_with_retry(
        X=X,
        y=y,
        variable_names=["x"],
        variable_descriptions={"x": "position"},
        variable_units={},
    )

    report = result["discovery_report"]
    assert report["status"] == "accepted"
    assert report["selected_candidate_id"] == report["candidates"][0]["candidate_id"]
    candidate = report["candidates"][0]
    assert candidate["metrics"]["training_validation"]["valid_fold_count"] == 2
    assert candidate["metrics"]["training_validation"]["selection_data_scope"] == "training_region_only"
    assert report["far_evaluation_used_for_selection"] is False
    assert result["candidate_selection_policy"] == "training_only_physics_gated_pareto"



def test_candidate_report_fails_closed_when_training_folds_cannot_be_built():
    import numpy as np

    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2, "maximum": 2}},
        constraints=(
            ConstraintSpec(
                constraint_id="energy-nonnegative",
                kind="nonnegative_output",
                severity="hard",
            ),
        ),
    )
    system = _system("x**2", problem)
    X = np.array([[-1.0], [0.0], [1.0]])
    y = np.square(X[:, 0])
    system._active_training_validation_settings = {"n_splits": 2}
    system._active_training_validation_seed = 42
    system._discover_X_orig = X
    system._discover_y_orig = y

    with pytest.raises(ValueError, match="NO_CREDIBLE_CANDIDATE"):
        system._discover_with_retry(
            X=X,
            y=y,
            variable_names=["x"],
            variable_descriptions={"x": "position"},
            variable_units={},
        )

    assert system._last_discovery_report["status"] == "insufficient_validation_evidence"
    assert system._last_discovery_report["selected_candidate_id"] is None
