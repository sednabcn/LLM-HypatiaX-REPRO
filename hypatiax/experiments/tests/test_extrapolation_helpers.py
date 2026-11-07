"""
test_extrapolation_helpers.py — real pytest unit tests for the deterministic
helper logic inside test_enhanced_defi_extrapolation.py.

Why this file exists
---------------------
`make test` / CI point pytest at hypatiax/experiments/tests/. The only file
there, test_enhanced_defi_extrapolation.py, is a 73-case benchmark *runner*
(needs PySR/Julia/torch/an Anthropic API key and takes hours) — it defines no
`def test_*` functions or `Test*` classes, so pytest silently collects 0
items and `make test` reports success without checking anything.

This file adds fast, deterministic unit tests for the pure helper methods
that don't require the heavy symbolic/NN backends: data-splitting, formula
routing heuristics, and the test-case catalogue itself. It also covers
`_eval_formula_r2`, whose import path was broken (see fix below) and which
always silently returned (nan, False) as a result.
"""

import numpy as np
import pytest

from hypatiax.experiments.tests.test_enhanced_defi_extrapolation import (
    EnhancedExtrapolationTest,
)


@pytest.fixture
def tester():
    return EnhancedExtrapolationTest()


# ─────────────────────────────────────────────────────────────────────────
# create_aggressive_split
# ─────────────────────────────────────────────────────────────────────────

class TestCreateAggressiveSplit:
    def test_high_split_trains_on_low_values(self, tester):
        rng = np.random.default_rng(0)
        X = rng.uniform(0, 100, size=(200, 1))
        y = X.flatten() * 2

        X_train, y_train, X_test, y_test = tester.create_aggressive_split(
            X, y, {"split_var_idx": 0, "split_type": "high"}
        )

        assert len(X_train) > 0 and len(X_test) > 0
        assert len(X_train) + len(X_test) <= len(X)
        # Train partition should skew toward lower values than test partition
        assert X_train.flatten().mean() < X_test.flatten().mean()

    def test_low_split_trains_on_high_values(self, tester):
        rng = np.random.default_rng(1)
        X = rng.uniform(0, 100, size=(200, 1))
        y = X.flatten() * 2

        X_train, y_train, X_test, y_test = tester.create_aggressive_split(
            X, y, {"split_var_idx": 0, "split_type": "low"}
        )

        assert len(X_train) > 0 and len(X_test) > 0
        assert X_train.flatten().mean() > X_test.flatten().mean()

    def test_handles_1d_input(self, tester):
        rng = np.random.default_rng(2)
        X = rng.uniform(0, 100, size=200)  # 1-D, not (200, 1)
        y = X * 3

        X_train, y_train, X_test, y_test = tester.create_aggressive_split(
            X, y, {"split_var_idx": 0, "split_type": "high"}
        )
        assert len(X_train) > 0 and len(X_test) > 0

    def test_falls_back_when_partitions_too_small(self, tester):
        # Tiny dataset: percentile split would leave < 20 rows in a partition,
        # so the method must fall back to the index-based 40/60 split.
        X = np.arange(10, dtype=float).reshape(-1, 1)
        y = X.flatten() * 2

        X_train, y_train, X_test, y_test = tester.create_aggressive_split(
            X, y, {"split_var_idx": 0, "split_type": "high"}
        )
        assert len(X_train) == 4          # int(0.4 * 10)
        assert len(X_test) == 6
        np.testing.assert_array_equal(X_train.flatten(), [0, 1, 2, 3])

    def test_multi_column_uses_correct_variable(self, tester):
        rng = np.random.default_rng(3)
        n = 200
        X = np.column_stack([
            rng.uniform(0, 100, n),   # col 0
            rng.uniform(0, 1, n),     # col 1 — irrelevant to the split
        ])
        y = X[:, 0] * 2

        X_train, y_train, X_test, y_test = tester.create_aggressive_split(
            X, y, {"split_var_idx": 0, "split_type": "high"}
        )
        assert X_train[:, 0].mean() < X_test[:, 0].mean()


# ─────────────────────────────────────────────────────────────────────────
# _formula_has_transcendental
# ─────────────────────────────────────────────────────────────────────────

class TestFormulaHasTranscendental:
    @pytest.mark.parametrize("code", [
        "def formula(x0): return np.exp(x0)",
        "def formula(x0): return math.log(x0)",
        "def formula(x0): return np.sqrt(x0)",
        "def formula(x0): return norm.cdf(x0)",
        "def formula(x0): return np.maximum(x0, 0)",
        "def formula(x0): return x0**0.5",
        "def formula(x0): return np.sin(x0) + np.cos(x0)",
    ])
    def test_detects_transcendental_tokens(self, code):
        assert EnhancedExtrapolationTest._formula_has_transcendental(code) is True

    @pytest.mark.parametrize("code", [
        "def formula(x0): return 2 * x0",
        "def formula(x0, x1): return x0 + x1 - 3",
        "def formula(x0): return x0 * x0",
    ])
    def test_plain_polynomial_is_not_transcendental(self, code):
        assert EnhancedExtrapolationTest._formula_has_transcendental(code) is False

    def test_is_case_insensitive(self):
        assert EnhancedExtrapolationTest._formula_has_transcendental(
            "def formula(x0): return NP.EXP(x0)"
        ) is True


# ─────────────────────────────────────────────────────────────────────────
# _distance_llm_weight
# ─────────────────────────────────────────────────────────────────────────

class TestDistanceLlmWeight:
    def test_in_distribution_gives_base_weight(self):
        X_train = np.array([[0.0], [10.0]])
        X_test = np.array([[5.0]])   # fully inside [0, 10]
        w = EnhancedExtrapolationTest._distance_llm_weight(
            X_test, X_train, base_weight=0.3
        )
        assert w == pytest.approx(0.3)

    def test_fully_out_of_distribution_gives_weight_one(self):
        X_train = np.array([[0.0], [10.0]])
        X_test = np.array([[100.0]])  # outside range
        w = EnhancedExtrapolationTest._distance_llm_weight(
            X_test, X_train, base_weight=0.3
        )
        assert w == pytest.approx(1.0)

    def test_partial_out_of_distribution_is_between_bounds(self):
        X_train = np.array([[0.0], [10.0]])
        X_test = np.array([[5.0], [20.0]])  # 1 of 2 points out of range
        w = EnhancedExtrapolationTest._distance_llm_weight(
            X_test, X_train, base_weight=0.3
        )
        assert 0.3 < w < 1.0

    def test_handles_1d_arrays(self):
        X_train = np.array([0.0, 10.0])
        X_test = np.array([50.0])
        w = EnhancedExtrapolationTest._distance_llm_weight(X_test, X_train)
        assert w == pytest.approx(1.0)


# ─────────────────────────────────────────────────────────────────────────
# _eval_formula_r2
# regression test for the broken-import bug (see git history / fix notes):
# the method's `from hypatiax.experiments.tests.hybrid_ensemble_system_defi_domain
# import execute_python_code_get_predictions` pointed at a module that doesn't
# exist, so the surrounding bare `except Exception` swallowed the
# ModuleNotFoundError and every call silently returned (nan, False).
# ─────────────────────────────────────────────────────────────────────────

class TestEvalFormulaR2:
    def test_perfect_formula_returns_r2_one(self):
        X = np.array([[1.0], [2.0], [3.0], [4.0]])
        y = np.array([2.0, 4.0, 6.0, 8.0])
        r2, success = EnhancedExtrapolationTest._eval_formula_r2(
            "def formula(x0): return 2 * x0", X, y, ["x0"]
        )
        assert success is True
        assert r2 == pytest.approx(1.0, abs=1e-9)

    def test_import_path_resolves(self):
        # Directly exercises the fixed import path so a future regression
        # (e.g. someone reverting the path) fails loudly here instead of
        # silently degrading to (nan, False) inside a bare except.
        from hypatiax.core.generation.hybrid_defi_llm_nn.hybrid_ensemble_system_defi_domain import (
            execute_python_code_get_predictions,
        )
        X = np.array([[1.0], [2.0]])
        preds = execute_python_code_get_predictions(
            "def formula(x0): return x0 + 1", X
        )
        np.testing.assert_allclose(preds, [2.0, 3.0])


# ─────────────────────────────────────────────────────────────────────────
# get_test_cases — catalogue sanity checks
# ─────────────────────────────────────────────────────────────────────────

class TestGetTestCases:
    REQUIRED_KEYS = {"name", "domain", "difficulty", "formula_type",
                      "num_samples", "config"}

    def test_docstring_case_count_matches_reality(self, tester):
        cases = tester.get_test_cases()
        # The module docstring and class docstring both claim 73 cases.
        assert len(cases) == 73, (
            f"get_test_cases() returned {len(cases)} cases; module docs claim 73. "
            "Update the docstrings or the catalogue so they agree."
        )

    def test_every_case_has_required_fields(self, tester):
        for case in tester.get_test_cases():
            missing = self.REQUIRED_KEYS - case.keys()
            assert not missing, f"case {case.get('name')!r} missing keys: {missing}"

    def test_case_names_are_unique(self, tester):
        names = [c["name"] for c in tester.get_test_cases()]
        dupes = {n for n in names if names.count(n) > 1}
        assert not dupes, f"duplicate case names: {dupes}"

    def test_split_config_has_valid_type(self, tester):
        for case in tester.get_test_cases():
            split_type = case["config"].get("split_type")
            assert split_type in ("high", "low"), (
                f"case {case['name']!r} has invalid split_type={split_type!r}"
            )



# ─────────────────────────────────────────────────────────────────────────
# Portfolio PCA split protocol — opt-in audit metadata and exact case identity
# ─────────────────────────────────────────────────────────────────────────

class TestPortfolioPcaSplitProtocol:
    def test_pca_split_keeps_feature_target_rows_aligned_and_reports_metadata(self):
        from hypatiax.tools.utils.pca_split_utils import pca_directed_split

        n = 100
        X = np.column_stack([np.linspace(1000, 5000, n), np.linspace(-1, 1, n)])
        y = np.arange(n) * 7
        X_train, X_test, y_train, y_test, audit = pca_directed_split(
            X, y, test_size=0.6, random_state=42,
            feature_names=["notional", "correlation"], return_metadata=True,
        )

        assert len(X_train) == 40
        assert len(X_test) == 60
        # Targets encode original row positions; reconstruct them from the first feature.
        train_rows = np.rint((X_train[:, 0] - 1000) * 99 / 4000).astype(int)
        test_rows = np.rint((X_test[:, 0] - 1000) * 99 / 4000).astype(int)
        np.testing.assert_array_equal(y_train, train_rows * 7)
        np.testing.assert_array_equal(y_test, test_rows * 7)
        assert audit["split_protocol"] == "pca_40_60_pc1"
        assert audit["split_is_transductive"] is True
        assert audit["feature_scaling"] == "none"
        assert audit["n_train"] == 40 and audit["n_test"] == 60
        assert set(audit["pc1_loadings"]) == {"notional", "correlation"}
        assert audit["pc1_explained_variance_ratio"] > 0.99

    def test_default_return_shape_remains_backward_compatible(self):
        from hypatiax.tools.utils.pca_split_utils import pca_directed_split

        X = np.arange(40, dtype=float).reshape(20, 2)
        y = np.arange(20)
        result = pca_directed_split(X, y, test_size=0.6, random_state=42)
        assert len(result) == 4

    def test_feature_name_count_is_validated_when_auditing(self):
        from hypatiax.tools.utils.pca_split_utils import pca_directed_split

        X = np.arange(40, dtype=float).reshape(20, 2)
        y = np.arange(20)
        with pytest.raises(ValueError, match="feature_names"):
            pca_directed_split(
                X, y, feature_names=["only_one"], return_metadata=True
            )

    def test_exact_case_identity_selects_portfolio_var_not_a_fuzzy_match(self):
        from hypatiax.tools.utils.pca_split_utils import select_case_by_identity

        cases = [
            {"domain": "risk_var", "name": "Annualised Portfolio tracking error"},
            {"domain": "risk_var", "name": "Portfolio VaR for two correlated assets"},
            {"domain": "risk", "name": "Portfolio VaR for two correlated assets"},
        ]
        index, selected = select_case_by_identity(
            cases, "risk_var", "Portfolio VaR for two correlated assets"
        )
        assert index == 1
        assert selected is cases[1]

    def test_legacy_first_feature_split_is_preserved_and_not_transductive(self):
        from hypatiax.tools.utils.pca_split_utils import first_feature_percentile_split

        X = np.column_stack([np.arange(100, dtype=float), np.arange(100, dtype=float)[::-1]])
        y = np.arange(100) * 5
        X_train, y_train, X_test, y_test, audit = first_feature_percentile_split(
            X, y, return_metadata=True
        )

        assert len(X_train) == 40 and len(X_test) == 60
        assert X_train[:, 0].max() == 39
        assert X_test[:, 0].min() == 40
        np.testing.assert_array_equal(y_train, X_train[:, 0] * 5)
        np.testing.assert_array_equal(y_test, X_test[:, 0] * 5)
        assert audit["split_protocol"] == "first_feature_percentile_40_60"
        assert audit["split_is_transductive"] is False

    def test_protocol_contains_the_exact_portfolio_var_case(self):
        from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
        from hypatiax.tools.utils.pca_split_utils import select_case_by_identity

        protocol = DeFiExperimentProtocol()
        rows = [
            {
                "domain": "risk_var",
                "name": row[0],
                "description": row[0],
            }
            for row in protocol.load_test_data("risk_var", num_samples=200)
        ]
        index, selected = select_case_by_identity(
            rows, "risk_var", "Portfolio VaR for two correlated assets"
        )
        assert index >= 0
        assert selected["name"] == "Portfolio VaR for two correlated assets"

    def test_exact_case_identity_rejects_missing_or_duplicate_cases(self):
        from hypatiax.tools.utils.pca_split_utils import select_case_by_identity

        with pytest.raises(ValueError, match="found 0"):
            select_case_by_identity([], "risk_var", "Portfolio VaR for two correlated assets")
        duplicate = [
            {"domain": "risk_var", "name": "Portfolio VaR for two correlated assets"},
            {"domain": "risk_var", "name": "Portfolio VaR for two correlated assets"},
        ]
        with pytest.raises(ValueError, match="found 2"):
            select_case_by_identity(
                duplicate, "risk_var", "Portfolio VaR for two correlated assets"
            )
