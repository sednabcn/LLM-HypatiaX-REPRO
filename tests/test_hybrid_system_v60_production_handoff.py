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
    calibrate_frozen_native_v60_model,
    predict_frozen_native_v60_interval,
    verify_final_model_audit,
)


def _audit(model):
    # Complete compact fixtures to the same semantic contract emitted by the
    # native finalizer; callers below can then mutate/reseal individual fields.
    expressions = model["basis_expressions"]
    ids = model["basis_candidate_ids"]
    model.setdefault("family", "single_basis" if len(expressions) == 1 else "multi_basis")
    model.setdefault("candidate_id", ids[0] if len(expressions) == 1 else None)
    model.setdefault("candidate_group_id", None if len(expressions) == 1 else "g1")
    model.setdefault("training_row_count", 8)
    model.setdefault("training_target_std", 1.0)
    model.setdefault("training_rmse", 0.0)
    model.setdefault("training_nrmse", 0.0)
    model.setdefault("training_r2", 1.0)
    model.setdefault("training_design_rank", len(expressions) + 1)
    model.setdefault("training_design_condition_number", 1.0)
    model.setdefault("selection_metric", "cv_nrmse")
    model.setdefault("cross_validation_metric", 0.0)
    model.setdefault("cross_validation_metric_std", 0.0)
    model.setdefault("symbolic_complexity", 1 if len(expressions) == 1 else 3)
    option = {
        "family": model["family"],
        "candidate_id": model["candidate_id"],
        "candidate_group_id": model["candidate_group_id"],
        "candidate_ids": ids if len(expressions) > 1 else None,
        "expressions": expressions,
        "cv_rmse": 0.0,
        "cv_nrmse": 0.0,
        "cv_rmse_std": 0.0,
        "cv_nrmse_std": 0.0,
        "complexity": model["symbolic_complexity"],
    }
    encoded = json.dumps(model, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "schema": "v60_native_final_model_v1",
        "execution_status": "selected",
        "selection_performed": True,
        "far_or_evaluation_data_used": False,
        "objective_metric": "cv_nrmse",
        "candidate_options": [option],
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

    def test_self_rehashed_inconsistent_training_nrmse_is_rejected(self):
        model = {
            "basis_candidate_ids": ["c1"],
            "basis_expressions": ["x"],
            "variable_names": ["x"],
            "coefficients": [2.0, 1.0],
            "fitted_expression": "(2)*(x) + (1)",
        }
        audit = _audit(model)
        audit["selected_model"]["training_nrmse"] = 7.0
        encoded = json.dumps(audit["selected_model"], sort_keys=True, separators=(",", ":"), allow_nan=False)
        audit["selected_model_sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "training NRMSE"):
            verify_final_model_audit(audit)

    def test_self_rehashed_cross_family_option_substitution_is_rejected(self):
        model = {
            "basis_candidate_ids": ["c1"],
            "basis_expressions": ["x"],
            "variable_names": ["x"],
            "coefficients": [2.0, 1.0],
            "fitted_expression": "(2)*(x) + (1)",
        }
        audit = _audit(model)
        audit["candidate_options"][0]["cv_nrmse"] = 0.5
        with self.assertRaisesRegex(ValueError, "cross-family winner"):
            verify_final_model_audit(audit)

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

    def test_final_model_verifier_rejects_rank_deficient_training_design(self):
        X = np.arange(1.0, 9.0).reshape(-1, 1)
        y = 3.0 * X[:, 0] + 2.0
        candidates = [{
            "candidate_id": "c1",
            "expression": "x",
            "normalized_expression": "x",
            "producer_provenance": [],
        }]
        single = {
            "schema": "v60_native_objective_selection_v1",
            "selection_status": "selected",
            "selection_performed": True,
            "far_or_evaluation_data_used": False,
            "pareto_candidate_ids": ["c1"],
            "selected_candidate_id": "c1",
            "objective_evidence": [{
                "candidate_id": "c1", "expression": "x",
                "mean_validation_rmse": 0.0, "mean_validation_nrmse": 0.0,
                "std_validation_rmse": 0.0, "std_validation_nrmse": 0.0,
                "complexity": 1,
            }],
        }
        evidence = single["objective_evidence"][0]
        digest = hashlib.sha256(
            json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        evidence["objective_evidence_sha256"] = digest
        single["selected_objective_evidence_sha256"] = digest
        multi = {"selection_status": "no_credible_candidate", "objective_evidence": []}
        final = finalize_native_v60_model(
            candidates, single, multi, X, y, variable_names=["x"]
        )
        final["selected_model"]["training_design_rank"] = 1
        encoded = json.dumps(
            final["selected_model"], sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        final["selected_model_sha256"] = hashlib.sha256(encoded.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "full column rank"):
            verify_final_model_audit(final)


if __name__ == "__main__":
    unittest.main()



class NativeV60SplitConformalTests(unittest.TestCase):
    def _frozen_model(self):
        X = np.arange(1.0, 9.0).reshape(-1, 1)
        y = 3.0 * X[:, 0] + 2.0
        candidates = [{
            "candidate_id": "c1", "expression": "x",
            "normalized_expression": "x", "producer_provenance": [],
        }]
        single = {
            "selection_status": "selected", "selected_candidate_id": "c1",
            "objective_evidence": [{
                "candidate_id": "c1", "expression": "x",
                "mean_validation_rmse": 0.0, "mean_validation_nrmse": 0.0,
                "std_validation_rmse": 0.0, "std_validation_nrmse": 0.0,
                "complexity": 1,
            }],
        }
        multi = {"selection_status": "no_credible_candidate", "objective_evidence": []}
        return finalize_native_v60_model(
            candidates, single, multi, X, y, variable_names=["x"]
        )

    def test_split_conformal_calibrates_and_predicts_without_changing_model(self):
        final = self._frozen_model()
        X_cal = np.arange(20.0, 39.0).reshape(-1, 1)
        predictions = 3.0 * X_cal[:, 0] + 2.0
        residuals = np.arange(1.0, 20.0)
        provenance = {
            "training_split_id": "train-v1",
            "calibration_split_id": "cal-v1",
            "disjoint_from_training": True,
            "exchangeability_assumed": True,
        }
        calibration = calibrate_frozen_native_v60_model(
            final, X_cal, predictions + residuals, variable_names=["x"],
            nominal_coverage=0.95, calibration_provenance=provenance,
        )
        assert calibration["calibration_status"] == "calibrated"
        assert calibration["finite_sample_quantile_rank"] == 19
        assert calibration["interval_radius"] == 19.0
        X_new = np.asarray([[40.0], [41.0]])
        intervals = predict_frozen_native_v60_interval(
            final, calibration, X_new, variable_names=["x"],
        )
        assert intervals["lower"][0] == 3.0 * 40.0 + 2.0 - 19.0
        assert intervals["upper"][0] == 3.0 * 40.0 + 2.0 + 19.0
        assert intervals["coverage_claim"] == "finite_sample_marginal_coverage_under_exchangeability"
        assert intervals["extra_domain_or_distribution_shift_guarantee"] is False
        assert calibration["selection_changed"] is False

    def test_small_calibration_split_does_not_emit_finite_interval(self):
        final = self._frozen_model()
        X_cal = np.asarray([[20.0], [21.0], [22.0]])
        y_cal = 3.0 * X_cal[:, 0] + 2.0
        calibration = calibrate_frozen_native_v60_model(
            final, X_cal, y_cal, variable_names=["x"],
            nominal_coverage=0.95,
            calibration_provenance={
                "training_split_id": "train-v1",
                "calibration_split_id": "cal-v1",
                "disjoint_from_training": True,
                "exchangeability_assumed": True,
            },
        )
        assert calibration["calibration_status"] == "insufficient_calibration_size"
        assert calibration["interval_radius"] is None
        with self.assertRaisesRegex(ValueError, "finite-radius"):
            predict_frozen_native_v60_interval(
                final, calibration, np.asarray([[23.0]]), variable_names=["x"],
            )

    def test_calibration_requires_disjoint_exchangeable_split_attestation(self):
        final = self._frozen_model()
        X_cal = np.asarray([[20.0], [21.0], [22.0]])
        y_cal = 3.0 * X_cal[:, 0] + 2.0
        with self.assertRaisesRegex(ValueError, "distinct"):
            calibrate_frozen_native_v60_model(
                final, X_cal, y_cal, variable_names=["x"],
                calibration_provenance={
                    "training_split_id": "same",
                    "calibration_split_id": "same",
                    "disjoint_from_training": True,
                    "exchangeability_assumed": True,
                },
            )
