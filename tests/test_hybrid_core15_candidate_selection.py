"""Regression: typed candidate selection must not trust the compatibility winner."""
from types import SimpleNamespace

import numpy as np

from hypatiax.experiments.benchmarks.exp1_ablation_contracts import (
    build_core15_discovery_problem,
)
from hypatiax.tools.symbolic.discovery_validation import CandidateValidator
from hypatiax.tools.symbolic.hybrid_system_v50_2 import HybridDiscoverySystem


class _FakeSymbolicEngine:
    def __init__(self):
        self.config = SimpleNamespace(
            use_transcendental_compositions=False,
            unary_operators=[],
        )
        self.llm_engine = None

    def discover(self, *args, **kwargs):
        raise AssertionError("test must install its candidate-envelope fixture")


def _system(problem):
    system = HybridDiscoverySystem.__new__(HybridDiscoverySystem)
    system.symbolic_engine = _FakeSymbolicEngine()
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


def test_training_only_pareto_selects_valid_llm_hypothesis_over_bad_compatibility_winner():
    variables = ["n", "T", "V"]
    equation = {
        "name": "Ideal Gas Law",
        "domain": "Physics",
        "vars": variables,
        "train_range": [(0.1, 5.0), (200.0, 500.0), (0.01, 1.0)],
    }
    problem = build_core15_discovery_problem(equation, variables, seed=42)
    system = _system(problem)

    rng = np.random.default_rng(42)
    X = np.column_stack((
        rng.uniform(0.1, 5.0, 60),
        rng.uniform(200.0, 500.0, 60),
        rng.uniform(0.01, 1.0, 60),
    ))
    y = X[:, 0] * X[:, 1] / X[:, 2]
    system._active_training_validation_settings = {
        "n_splits": 2,
        "validation_fraction": 0.2,
        "minimum_valid_folds": 2,
        "minimum_candidate_pool_size": 1,
        "coefficient_max_nfev": 500,
    }
    system._active_training_validation_seed = 42
    system._discover_X_orig = X
    system._discover_y_orig = y
    system.symbolic_engine._predict_from_equation = (
        lambda expression, values, names: (
            values[:, names.index("n")] * values[:, names.index("T")]
            / values[:, names.index("V")]
        )
    )
    identity = {
        "input_feature_count": 3,
        "x_scales": [1.0, 1.0, 1.0],
        "gm_pairs": [],
        "ratio_pairs": [],
        "y_std": 1.0,
        "feature_names": variables,
        "transform_source": "test_identity",
    }
    system.symbolic_engine.discover = lambda *args, **kwargs: {
        # Deliberately invalid legacy compatibility winner.
        "expression": "sqrt(n*5.4327)",
        "r2_score": 0.999,
        "llm_mode": "hybrid_pysr_better",
        "discovery_candidates_schema": "discovery_candidates_v1",
        "discovery_candidates": [
            {
                "candidate_id": "ideal-gas-llm",
                "expression": "n*T/V",
                "fit_expression": "n*T/V",
                "fit_variable_names": variables,
                "fit_transform_state": identity,
                "source": "llm_proposal",
                "source_provenance": [{"source": "llm_proposal", "strategy": "llm_hypothesis"}],
                "search_strategy": "llm_hypothesis",
                "seed": 42,
            },
            {
                "candidate_id": "ideal-gas-pysr",
                "expression": "sqrt(n*5.4327)",
                "fit_expression": "sqrt(n*5.4327)",
                "fit_variable_names": variables,
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
            "deduplicated_candidate_count": 2,
        },
    }

    result = system._discover_with_retry(
        X=X,
        y=y,
        variable_names=variables,
        variable_descriptions={name: name for name in variables},
        variable_units={},
        equation_name="Ideal Gas Law",
    )

    report = result["discovery_report"]
    assert report["status"] == "accepted"
    assert result["candidate_source"] == "llm_proposal"
    assert all(name in result["expression"] for name in variables)
    assert "sqrt" not in result["expression"].lower()
    candidates = {item["source"]: item for item in report["candidates"]}
    assert candidates["llm_proposal"]["eligible"] is True
    assert candidates["pysr_search"]["eligible"] is False
    assert "required input variable" in " ".join(
        candidates["pysr_search"]["rejection_reasons"]
    )
