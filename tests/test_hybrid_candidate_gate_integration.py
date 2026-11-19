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
                severity="soft",
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



def test_engine_candidate_with_engineered_feature_passes_gate_and_fold_report():
    import numpy as np

    problem = DiscoveryProblem(
        target_name="amplitude",
        variable_names=("a", "b"),
        variable_domains={
            "a": {"minimum": 1.0, "maximum": 5.0},
            "b": {"minimum": 2.0, "maximum": 8.0},
        },
        constraints=(
            ConstraintSpec(
                constraint_id="amplitude-nonnegative",
                kind="nonnegative_output",
                severity="hard",
            ),
        ),
    )
    system = _system("annotated display only", problem)
    system.symbolic_engine.discover = lambda *args, **kwargs: {
        "expression": "[X-normalised: none] 1.0*gm_a_b",
        "fit_expression": "1.0*gm_a_b",
        "fit_variable_names": ["a", "b", "gm_a_b"],
        "fit_transform_state": {
            "x_scales": [1.0, 1.0],
            "gm_pairs": [[0, 1]],
            "ratio_pairs": [],
            "y_std": 1.0,
        },
        "variable_names": ["a", "b", "gm_a_b"],
        "r2_score": 0.999999,
        "llm_mode": "none",
    }
    a = np.linspace(1.0, 5.0, 30)
    b = np.linspace(2.0, 8.0, 30)
    X = np.column_stack((a, b))
    y = 2.5 * np.sqrt(a * b)
    system._active_training_validation_settings = {
        "n_splits": 2,
        "validation_fraction": 0.2,
        "minimum_valid_folds": 2,
    }
    system._active_training_validation_seed = 43
    system._discover_X_orig = X
    system._discover_y_orig = y

    result = system._discover_with_retry(
        X=X,
        y=y,
        variable_names=["a", "b"],
        variable_descriptions={"a": "first amplitude", "b": "second amplitude"},
        variable_units={},
    )

    report = result["discovery_report"]
    assert report["status"] == "accepted"
    candidate = report["candidates"][0]
    assert candidate["eligible"] is True
    assert "sqrt" in candidate["expression"]
    assert candidate["metrics"]["training_validation"]["valid_fold_count"] == 2
    assert result["candidate_selection_policy"] == "training_only_physics_gated_pareto"



def test_llm_selected_candidate_exposes_identity_inner_transform_contract():
    import numpy as np
    from hypatiax.tools.symbolic.symbolic_engine import SymbolicEngineWithLLM

    engine = SymbolicEngineWithLLM.__new__(SymbolicEngineWithLLM)
    engine.llm_mode = "hybrid"
    engine.llm_engine = SimpleNamespace(config=SimpleNamespace(enabled=True))
    engine.model = None
    engine._discover_hybrid = lambda *args, **kwargs: {
        "expression": "0.5*x",
        "r2_score": 0.99,
        "variable_names": ["x"],
        "llm_mode": "hybrid_llm_better",
    }

    result = engine.discover(
        np.array([[1.0], [2.0], [3.0], [4.0]]),
        np.array([0.5, 1.0, 1.5, 2.0]),
        variable_names=["x"],
        equation_name="linear response",
    )

    assert result["fit_expression"] == "0.5*x"
    assert result["fit_variable_names"] == ["x"]
    assert result["fit_transform_state"]["x_scales"] == [1.0]
    assert result["fit_transform_state"]["y_std"] == 1.0
    assert result["fit_transform_state"]["transform_source"] == (
        "llm_outer_fit_space_identity_inner_transform"
    )



def test_llm_selected_retry_candidate_is_attributed_to_llm_proposal():
    import numpy as np

    problem = DiscoveryProblem(target_name="energy", variable_names=("x",))
    system = _system("0.5*x", problem)
    system.symbolic_engine.discover = lambda *args, **kwargs: {
        "expression": "0.5*x",
        "r2_score": 0.999999,
        "llm_mode": "hybrid_llm_better",
    }
    observed_sources = []
    original_validate = system._candidate_validator.validate

    def capture_source(problem, expression, **kwargs):
        observed_sources.append(kwargs.get("source"))
        return original_validate(problem, expression, **kwargs)

    system._candidate_validator.validate = capture_source
    result = system._discover_with_retry(
        X=np.array([[1.0], [2.0], [3.0]]),
        y=np.array([0.5, 1.0, 1.5]),
        variable_names=["x"],
        variable_descriptions={"x": "input"},
        variable_units={},
    )

    assert result["candidate_source"] == "llm_proposal"
    assert observed_sources == ["llm_proposal"]


def test_typed_retry_early_stop_waits_for_distinct_candidate_pool():
    import numpy as np

    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2.0, "maximum": 2.0}},
    )
    system = _system("x**2", problem)
    system.max_retries = 3
    expressions = iter(("x**2", "x**2 + 0", "x**2"))
    calls = []

    def discover(*args, **kwargs):
        calls.append(True)
        return {
            "expression": next(expressions),
            "r2_score": 0.999999,
            "llm_mode": "none",
        }

    system.symbolic_engine.discover = discover
    X = np.linspace(-2.0, 2.0, 30).reshape(-1, 1)
    y = np.square(X[:, 0])
    system._active_training_validation_settings = {
        "n_splits": 2,
        "validation_fraction": 0.2,
        "minimum_valid_folds": 2,
        "minimum_candidate_pool_size": 2,
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

    assert len(calls) == 2
    coverage = result["discovery_report"]["provenance"]["candidate_pool_coverage"]
    assert coverage["distinct_eligible_expressions"] == 2
    assert coverage["minimum_for_early_stop"] == 2


def test_typed_retry_consumes_each_inner_llm_and_pysr_candidate_independently():
    import numpy as np

    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2.0, "maximum": 2.0}},
    )
    system = _system("x**2", problem)
    system.symbolic_engine._predict_from_equation = (
        lambda expression, X, names: np.square(np.asarray(X)[:, 0])
    )
    identity = {
        "input_feature_count": 1,
        "x_scales": [1.0],
        "gm_pairs": [],
        "ratio_pairs": [],
        "y_std": 1.0,
        "feature_names": ["x"],
        "transform_source": "test_identity",
    }
    system.symbolic_engine.discover = lambda *args, **kwargs: {
        "expression": "x**2",
        "r2_score": 0.999,
        "llm_mode": "hybrid_pysr_better",
        "discovery_candidates_schema": "discovery_candidates_v1",
        "discovery_candidates": [
            {
                "candidate_id": "inner-llm-1",
                "expression": "x**2",
                "fit_expression": "x**2",
                "fit_variable_names": ["x"],
                "fit_transform_state": identity,
                "source": "llm_proposal",
                "source_provenance": [{"source": "llm_proposal", "strategy": "llm_hypothesis"}],
                "search_strategy": "llm_hypothesis",
                "seed": 42,
            },
            {
                "candidate_id": "inner-pysr-1",
                "expression": "x*x",
                "fit_expression": "x*x",
                "fit_variable_names": ["x"],
                "fit_transform_state": identity,
                "source": "pysr_search",
                "source_provenance": [{"source": "pysr_search", "strategy": "pysr_refinement"}],
                "search_strategy": "pysr_refinement",
                "seed": 42,
            },
        ],
        "discovery_candidate_generation": {
            "llm_hypotheses_observed": 1,
            "pysr_search_generated_candidate": True,
            "pysr_skipped_by_llm_acceptance": False,
        },
    }
    X = np.linspace(-2.0, 2.0, 30).reshape(-1, 1)
    y = np.square(X[:, 0])
    system._active_training_validation_settings = {
        "n_splits": 2,
        "validation_fraction": 0.2,
        "minimum_valid_folds": 2,
        "minimum_candidate_pool_size": 2,
    }
    system._active_training_validation_seed = 42
    system._discover_X_orig = X
    system._discover_y_orig = y

    result = system._discover_with_retry(
        X=X,
        y=y,
        variable_names=["x"],
        variable_descriptions={"x": "input"},
        variable_units={},
    )

    report = result["discovery_report"]
    assert {candidate["source"] for candidate in report["candidates"]} == {
        "llm_proposal", "pysr_search"
    }
    assert all(
        candidate["metrics"]["training_validation"]["valid_fold_count"] == 2
        for candidate in report["candidates"]
    )
    assert report["provenance"]["multi_candidate_handoff_consumed"] is True
    assert report["provenance"]["candidate_source_counts"] == {
        "llm_proposal": 1, "pysr_search": 1
    }
    assert result["training_r2_role"] == "post_selection_diagnostic_only"


def test_hybrid_engine_emits_candidate_specific_llm_and_pysr_fit_contracts():
    import numpy as np
    from hypatiax.tools.symbolic.symbolic_engine import SymbolicEngineWithLLM

    engine = SymbolicEngineWithLLM.__new__(SymbolicEngineWithLLM)
    engine.llm_mode = "hybrid"
    engine.llm_engine = SimpleNamespace(config=SimpleNamespace(enabled=True))
    engine.model = None
    engine._discover_hybrid = lambda *args, **kwargs: {
        "expression": "x**2",
        "r2_score": 0.99,
        "variable_names": ["x"],
        "llm_mode": "hybrid_llm_better",
        "llm_hypotheses": ["x**2", "x**2"],
        "pysr_candidate": {
            "expression": "[X-normalised] x**3",
            "fit_expression": "x**3",
            "fit_variable_names": ["x"],
            "fit_transform_state": {
                "input_feature_count": 1,
                "x_scales": [2.0],
                "gm_pairs": [],
                "ratio_pairs": [],
                "y_std": 3.0,
                "feature_names": ["x"],
            },
        },
    }

    result = engine.discover(
        np.array([[1.0], [2.0], [3.0], [4.0]]),
        np.array([1.0, 4.0, 9.0, 16.0]),
        variable_names=["x"],
        equation_name="quadratic response",
        random_state=17,
    )

    candidates = result["discovery_candidates"]
    assert result["discovery_candidates_schema"] == "discovery_candidates_v1"
    assert [candidate["source"] for candidate in candidates] == [
        "llm_proposal", "pysr_search"
    ]
    assert candidates[0]["fit_transform_state"]["x_scales"] == [1.0]
    assert candidates[1]["fit_transform_state"]["x_scales"] == [2.0]
    assert result["discovery_candidate_generation"]["pysr_search_generated_candidate"] is True
    generation = result["discovery_candidate_generation"]
    assert generation["llm_hypotheses_observed"] == 2
    assert generation["llm_hypotheses_admitted"] == 1
    assert generation["llm_hypotheses_deduplicated"] == 1
    assert generation["deduplication_count"] == 1
    assert generation["raw_proposal_count"] == 3
    assert generation["deduplicated_candidate_count"] == 2
    assert result["expression"] == "x**2"


def test_inner_candidate_gate_exception_is_retained_as_ineligible_report_record():
    import numpy as np

    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2.0, "maximum": 2.0}},
    )
    system = _system("x**2", problem)
    original_validate = system._candidate_validator.validate

    def fail_llm_gate(problem, expression, **kwargs):
        if kwargs.get("source") == "llm_proposal":
            raise RuntimeError("synthetic validator failure")
        return original_validate(problem, expression, **kwargs)

    system._candidate_validator.validate = fail_llm_gate
    identity = {
        "input_feature_count": 1,
        "x_scales": [1.0],
        "gm_pairs": [],
        "ratio_pairs": [],
        "y_std": 1.0,
        "feature_names": ["x"],
        "transform_source": "test_identity",
    }
    system.symbolic_engine.discover = lambda *args, **kwargs: {
        "expression": "x**2",
        "r2_score": 0.999,
        "llm_mode": "hybrid_pysr_better",
        "discovery_candidates_schema": "discovery_candidates_v1",
        "discovery_candidates": [
            {
                "candidate_id": "inner-llm-fails-gate",
                "expression": "x**2",
                "fit_expression": "x**2",
                "fit_variable_names": ["x"],
                "fit_transform_state": identity,
                "source": "llm_proposal",
                "source_provenance": [
                    {"source": "llm_proposal", "strategy": "llm_hypothesis"}
                ],
                "search_strategy": "llm_hypothesis",
                "seed": 42,
            },
            None,
            None,
            {
                "candidate_id": "inner-pysr-passes-gate",
                "expression": "x*x",
                "fit_expression": "x*x",
                "fit_variable_names": ["x"],
                "fit_transform_state": identity,
                "source": "pysr_search",
                "source_provenance": [
                    {"source": "pysr_search", "strategy": "pysr_refinement"}
                ],
                "search_strategy": "pysr_refinement",
                "seed": 42,
            },
        ],
    }
    X = np.linspace(-2.0, 2.0, 30).reshape(-1, 1)
    y = np.square(X[:, 0])
    system._active_training_validation_settings = {
        "n_splits": 2,
        "validation_fraction": 0.2,
        "minimum_valid_folds": 2,
        "minimum_candidate_pool_size": 2,
    }
    system._active_training_validation_seed = 42
    system._discover_X_orig = X
    system._discover_y_orig = y

    result = system._discover_with_retry(
        X=X,
        y=y,
        variable_names=["x"],
        variable_descriptions={"x": "input"},
        variable_units={},
    )

    report_candidates = result["discovery_report"]["candidates"]
    failed = next(item for item in report_candidates if item["source"] == "llm_proposal")
    assert failed["eligible"] is False
    assert failed["metrics"]["validation_execution"] == "not_completed"
    assert "synthetic validator failure" in " ".join(failed["rejection_reasons"])
    assert any(item["source"] == "pysr_search" and item["eligible"] for item in report_candidates)
    malformed = next(item for item in report_candidates if item["source"] == "unknown")
    assert malformed["eligible"] is False
    assert "malformed_candidate_envelope_item:1" in " ".join(malformed["rejection_reasons"])
    envelope_audit = result["discovery_report"]["provenance"]["candidate_envelope_audit"]
    assert envelope_audit["declared_item_count"] == 3
    assert envelope_audit["retained_item_count"] == 3
    assert envelope_audit["malformed_item_count"] == 1
    assert envelope_audit["ingestion_failure_count"] == 1
    assert envelope_audit["ingestion_complete"] is False
