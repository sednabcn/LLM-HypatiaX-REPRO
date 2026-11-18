"""Offline regression tests for the native V60 frozen production handoff."""
import hashlib
import json
import unittest
from unittest.mock import patch

import numpy as np

from hypatiax.tools.symbolic.hybrid_system_v50_2 import HybridDiscoverySystem
from hypatiax.tools.symbolic.hybrid_system_v60 import HybridDiscoverySystemV60
from hypatiax.tools.symbolic.v60_native_finalization import finalize_native_v60_model
from hypatiax.tools.symbolic.v60_production_handoff import (
    evaluate_frozen_native_v60_model,
    verify_final_model_audit,
)


def _audit(model):
    encoded = json.dumps(model, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "schema": "v60_native_final_model_v1",
        "execution_status": "selected",
        "selection_performed": True,
        "far_or_evaluation_data_used": False,
        "selected_model": model,
        "selected_model_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    }


class NativeV60ProductionHandoffTests(unittest.TestCase):
    def test_stage18_model_can_be_frozen_and_evaluated_after_selection(self):
        X = np.arange(1.0, 9.0).reshape(-1, 1)
        y = 3.0 * X[:, 0] + 2.0
        candidates = [{
            "candidate_id": "c1",
            "expression": "x",
            "normalized_expression": "x",
            "producer_provenance": [],
        }]
        single = {
            "selection_status": "selected",
            "selected_candidate_id": "c1",
            "objective_evidence": [{
                "candidate_id": "c1",
                "expression": "x",
                "mean_validation_rmse": 0.0,
                "mean_validation_nrmse": 0.0,
                "std_validation_rmse": 0.0,
                "std_validation_nrmse": 0.0,
                "complexity": 1,
            }],
        }
        multi = {"selection_status": "no_credible_candidate", "objective_evidence": []}
        final = finalize_native_v60_model(
            candidates, single, multi, X, y, variable_names=["x"]
        )
        verified = verify_final_model_audit(final)
        self.assertEqual(verified["basis_expressions"], ["x"])
        far = np.array([[9.0], [10.0]])
        result = evaluate_frozen_native_v60_model(
            final, far, 3.0 * far[:, 0] + 2.0, variable_names=["x"]
        )
        self.assertEqual(result["evaluation_status"], "completed")
        self.assertAlmostEqual(result["far_metrics"]["rmse"], 0.0, places=10)
        self.assertFalse(result["far_or_evaluation_data_used_for_selection"])
        self.assertFalse(result["selection_changed"])

    def test_frozen_evaluator_supports_joint_multi_basis_model(self):
        model = {
            "family": "multi_basis",
            "candidate_id": None,
            "candidate_group_id": "g1",
            "basis_candidate_ids": ["c1", "c2"],
            "basis_expressions": ["x", "x**2"],
            "variable_names": ["x"],
            "fitted_expression": "(2)*(x) + (3)*(x**2) + (1)",
            "coefficients": [2.0, 3.0, 1.0],
            "training_row_count": 8,
            "training_target_std": 1.0,
            "training_rmse": 0.0,
            "training_nrmse": 0.0,
            "training_r2": 1.0,
        }
        audit = _audit(model)
        far = np.array([[2.0], [3.0]])
        expected = 2.0 * far[:, 0] + 3.0 * far[:, 0] ** 2 + 1.0
        result = evaluate_frozen_native_v60_model(
            audit, far, expected, variable_names=["x"]
        )
        self.assertAlmostEqual(result["far_metrics"]["rmse"], 0.0, places=12)
        self.assertEqual(result["evaluation_scope"], "single_frozen_finalized_model")

    def test_frozen_evaluator_rejects_reordered_variable_contract(self):
        model = {
            "family": "single_basis",
            "candidate_id": "c1",
            "candidate_group_id": None,
            "basis_candidate_ids": ["c1"],
            "basis_expressions": ["x + 10*y"],
            "variable_names": ["x", "y"],
            "fitted_expression": "(1)*(x + 10*y) + (0)",
            "coefficients": [1.0, 0.0],
            "training_row_count": 8,
            "training_target_std": 1.0,
            "training_rmse": 0.0,
            "training_nrmse": 0.0,
            "training_r2": 1.0,
        }
        audit = _audit(model)
        with self.assertRaisesRegex(ValueError, "exactly match"):
            evaluate_frozen_native_v60_model(
                audit, np.array([[1.0, 2.0]]), np.array([21.0]),
                variable_names=["y", "x"],
            )

    def test_final_model_verifier_rejects_self_rehashed_formula_mismatch(self):
        model = {
            "family": "single_basis",
            "candidate_id": "c1",
            "candidate_group_id": None,
            "basis_candidate_ids": ["c1"],
            "basis_expressions": ["x"],
            "variable_names": ["x"],
            "fitted_expression": "999*x",
            "coefficients": [2.0, 1.0],
        }
        with self.assertRaisesRegex(ValueError, "fitted expression"):
            verify_final_model_audit(_audit(model))

    def test_tampered_final_model_is_rejected(self):
        audit = _audit({
            "basis_candidate_ids": ["c1"],
            "basis_expressions": ["x"],
            "variable_names": ["x"],
            "coefficients": [1.0, 0.0],
            "fitted_expression": "x",
        })
        audit["selected_model"]["coefficients"][0] = 99.0
        with self.assertRaisesRegex(ValueError, "digest"):
            verify_final_model_audit(audit)

    def test_native_handoff_does_not_call_legacy_discovery(self):
        engine = HybridDiscoverySystemV60(use_llm=False)
        X = np.arange(1.0, 5.0).reshape(-1, 1)
        y = 2.0 * X[:, 0]
        with patch.object(
            HybridDiscoverySystem,
            "discover",
            side_effect=AssertionError("legacy discovery must not run"),
        ):
            result = engine.discover(
                X, y, ["x"],
                metadata={"v60_activate_native_model": True},
            )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "NO_CREDIBLE_CANDIDATE")
        self.assertEqual(
            result["native_v60_production_handoff"]["status"],
            "blocked_no_credible_native_model",
        )

    def test_default_mode_still_delegates_to_v50_2(self):
        engine = HybridDiscoverySystemV60(use_llm=False)
        expected = {"success": True, "formula": "x"}
        with patch.object(HybridDiscoverySystem, "discover", return_value=expected) as legacy:
            result = engine.discover(
                np.arange(1.0, 5.0).reshape(-1, 1),
                np.arange(1.0, 5.0),
                ["x"],
            )
        legacy.assert_called_once()
        self.assertTrue(result["success"])
        self.assertEqual(result["formula"], "x")

    def test_legacy_entrypoint_clears_stale_native_handoff_state(self):
        engine = HybridDiscoverySystemV60(use_llm=False)
        engine._last_v60_activate_native_result = True
        engine._last_v60_run_context = object()
        engine._last_v60_candidate_proposals = ({"candidate_id": "stale"},)
        engine._last_v60_final_model_audit = {
            "execution_status": "selected",
            "selected_model": {"fitted_expression": "stale_native"},
        }
        expected = {"success": True, "formula": "legacy_formula"}
        with patch.object(
            HybridDiscoverySystem,
            "discover_validate_interpret",
            return_value=expected,
        ) as legacy:
            result = engine.discover_validate_interpret(
                np.arange(1.0, 5.0).reshape(-1, 1),
                np.arange(1.0, 5.0),
                ["x"],
                {"x": "input"},
                {"x": "dimensionless"},
            )
        legacy.assert_called_once()
        self.assertEqual(result["formula"], "legacy_formula")
        self.assertFalse(result["implementation_provenance"]["native_v60_pipeline"])
        self.assertFalse(result["implementation_provenance"]["native_v60_production_handoff_enabled"])
        self.assertIsNone(result["implementation_provenance"]["v60_run_context"])
        self.assertEqual(result["native_v60_candidate_proposals"], [])
        self.assertNotIn("native_v60_production_handoff", result)


if __name__ == "__main__":
    unittest.main()
