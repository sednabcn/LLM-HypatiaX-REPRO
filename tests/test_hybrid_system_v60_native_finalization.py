"""Offline regression tests for native V60 final model selection/refit."""
import hashlib
import json
import unittest

import numpy as np

from hypatiax.tools.symbolic.v60_native_finalization import finalize_native_v60_model


def _seal_selection(audit):
    evidence = audit["objective_evidence"][0]
    payload = dict(evidence)
    payload.pop("objective_evidence_sha256", None)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    evidence["objective_evidence_sha256"] = digest
    audit["selected_objective_evidence_sha256"] = digest
    return audit


class NativeV60FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.X = np.arange(1.0, 9.0).reshape(-1, 1)
        self.y = 3.0 * self.X[:, 0] + 2.0

    def test_single_basis_winner_is_refit_on_all_training_rows(self):
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
            "selected_objective_evidence_sha256": "a" * 64,
            "selected_candidate_id": "c1",
            "objective_evidence": [{
                "candidate_id": "c1", "expression": "x",
                "mean_validation_rmse": 0.0, "mean_validation_nrmse": 0.0,
                "std_validation_rmse": 0.0, "std_validation_nrmse": 0.0,
                "complexity": 1,
                "objective_evidence_sha256": "a" * 64,
            }],
        }
        _seal_selection(single)
        multi = {"selection_status": "no_credible_candidate", "objective_evidence": []}
        result = finalize_native_v60_model(
            candidates, single, multi, self.X, self.y, variable_names=["x"]
        )
        self.assertEqual(result["execution_status"], "selected")
        self.assertEqual(result["selected_model"]["family"], "single_basis")
        self.assertAlmostEqual(result["selected_model"]["training_rmse"], 0.0, places=10)
        self.assertFalse(result["far_or_evaluation_data_used"])

    def test_multi_basis_winner_preserves_ordered_basis_identity(self):
        candidates = [
            {"candidate_id": "c1", "normalized_expression": "x", "producer_provenance": []},
            {"candidate_id": "c2", "normalized_expression": "x**2", "producer_provenance": []},
        ]
        single = {"selection_status": "no_credible_candidate", "objective_evidence": []}
        multi = {
            "schema": "v60_native_multi_basis_objective_selection_v1",
            "selection_status": "selected",
            "selection_performed": True,
            "far_or_evaluation_data_used": False,
            "pareto_candidate_group_ids": ["g1"],
            "selected_objective_evidence_sha256": "b" * 64,
            "selected_candidate_group_id": "g1",
            "objective_evidence": [{
                "candidate_group_id": "g1",
                "basis_candidate_ids": ["c1", "c2"],
                "basis_expressions": ["x", "x**2"],
                "mean_validation_rmse": 0.0, "mean_validation_nrmse": 0.0,
                "std_validation_rmse": 0.0, "std_validation_nrmse": 0.0,
                "symbolic_complexity": 3,
                "objective_evidence_sha256": "b" * 64,
            }],
        }
        _seal_selection(multi)
        result = finalize_native_v60_model(
            candidates, single, multi, self.X, self.y, variable_names=["x"]
        )
        self.assertEqual(result["execution_status"], "selected")
        self.assertEqual(result["selected_model"]["family"], "multi_basis")
        self.assertEqual(result["selected_model"]["basis_candidate_ids"], ["c1", "c2"])
        self.assertAlmostEqual(result["selected_model"]["training_rmse"], 0.0, places=10)

    def test_no_selector_winner_returns_explicit_no_candidate(self):
        result = finalize_native_v60_model(
            [], {"selection_status": "no_credible_candidate", "objective_evidence": []},
            {"selection_status": "no_credible_candidate", "objective_evidence": []},
            self.X, self.y, variable_names=["x"]
        )
        self.assertEqual(result["execution_status"], "no_credible_candidate")
        self.assertIsNone(result["selected_model"])

    def test_cross_family_comparison_uses_common_error_metric(self):
        candidates = [
            {"candidate_id": "c1", "normalized_expression": "x", "producer_provenance": []},
            {"candidate_id": "c2", "normalized_expression": "x**2", "producer_provenance": []},
        ]
        single = {
            "schema": "v60_native_objective_selection_v1",
            "selection_status": "selected", "selected_candidate_id": "c1",
            "selection_performed": True, "far_or_evaluation_data_used": False,
            "pareto_candidate_ids": ["c1"], "selected_objective_evidence_sha256": "c" * 64,
            "objective_evidence": [{
                "candidate_id": "c1", "expression": "x",
                "mean_validation_rmse": 0.1, "mean_validation_nrmse": None,
                "std_validation_rmse": 0.01, "std_validation_nrmse": None,
                "complexity": 1, "objective_evidence_sha256": "c" * 64,
            }],
        }
        multi = {
            "schema": "v60_native_multi_basis_objective_selection_v1",
            "selection_status": "selected", "selected_candidate_group_id": "g2",
            "selection_performed": True, "far_or_evaluation_data_used": False,
            "pareto_candidate_group_ids": ["g2"], "selected_objective_evidence_sha256": "d" * 64,
            "objective_evidence": [{
                "candidate_group_id": "g2", "basis_candidate_ids": ["c1", "c2"],
                "basis_expressions": ["x", "x**2"],
                "mean_validation_rmse": 0.2, "mean_validation_nrmse": 0.001,
                "std_validation_rmse": 0.02, "std_validation_nrmse": 0.0001,
                "symbolic_complexity": 3, "objective_evidence_sha256": "d" * 64,
            }],
        }
        _seal_selection(single)
        _seal_selection(multi)
        result = finalize_native_v60_model(
            candidates, single, multi, self.X, self.y, variable_names=["x"]
        )
        self.assertEqual(result["objective_metric"], "cv_rmse")
        self.assertEqual(result["selected_model"]["family"], "single_basis")

    def test_finalizer_rejects_tampered_selected_objective_evidence(self):
        candidates = [{"candidate_id": "c1", "normalized_expression": "x", "producer_provenance": []}]
        single = {
            "schema": "v60_native_objective_selection_v1",
            "selection_status": "selected",
            "selection_performed": True,
            "far_or_evaluation_data_used": False,
            "pareto_candidate_ids": ["c1"],
            "selected_candidate_id": "c1",
            "objective_evidence": [{
                "candidate_id": "c1", "expression": "x",
                "mean_validation_rmse": 0.1, "mean_validation_nrmse": 0.1,
                "std_validation_rmse": 0.0, "std_validation_nrmse": 0.0,
                "complexity": 1,
            }],
        }
        _seal_selection(single)
        single["objective_evidence"][0]["mean_validation_rmse"] = 99.0
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            finalize_native_v60_model(
                candidates, single,
                {"selection_status": "no_credible_candidate", "objective_evidence": []},
                self.X, self.y, variable_names=["x"],
            )

    def test_finalizer_rejects_selected_candidate_outside_pareto_front(self):
        candidates = [{"candidate_id": "c1", "normalized_expression": "x", "producer_provenance": []}]
        single = {
            "schema": "v60_native_objective_selection_v1",
            "selection_status": "selected",
            "selection_performed": True,
            "far_or_evaluation_data_used": False,
            "pareto_candidate_ids": [],
            "selected_candidate_id": "c1",
            "objective_evidence": [{
                "candidate_id": "c1", "expression": "x",
                "mean_validation_rmse": 0.1, "mean_validation_nrmse": 0.1,
                "std_validation_rmse": 0.0, "std_validation_nrmse": 0.0,
                "complexity": 1,
            }],
        }
        _seal_selection(single)
        with self.assertRaisesRegex(ValueError, "Pareto front"):
            finalize_native_v60_model(
                candidates, single,
                {"selection_status": "no_credible_candidate", "objective_evidence": []},
                self.X, self.y, variable_names=["x"],
            )

    def test_rank_deficient_multi_basis_is_excluded_before_cross_family_choice(self):
        candidates = [
            {"candidate_id": "c1", "normalized_expression": "x", "producer_provenance": []},
            {"candidate_id": "c2", "normalized_expression": "2*x", "producer_provenance": []},
        ]
        single = {
            "schema": "v60_native_objective_selection_v1",
            "selection_status": "selected", "selection_performed": True,
            "far_or_evaluation_data_used": False, "pareto_candidate_ids": ["c1"],
            "selected_candidate_id": "c1",
            "objective_evidence": [{
                "candidate_id": "c1", "expression": "x",
                "mean_validation_rmse": 0.2, "mean_validation_nrmse": 0.2,
                "std_validation_rmse": 0.01, "std_validation_nrmse": 0.01,
                "complexity": 1,
            }],
        }
        multi = {
            "schema": "v60_native_multi_basis_objective_selection_v1",
            "selection_status": "selected", "selection_performed": True,
            "far_or_evaluation_data_used": False, "pareto_candidate_group_ids": ["g1"],
            "selected_candidate_group_id": "g1",
            "objective_evidence": [{
                "candidate_group_id": "g1", "basis_candidate_ids": ["c1", "c2"],
                "basis_expressions": ["x", "2*x"],
                "mean_validation_rmse": 0.01, "mean_validation_nrmse": 0.01,
                "std_validation_rmse": 0.001, "std_validation_nrmse": 0.001,
                "symbolic_complexity": 2,
            }],
        }
        _seal_selection(single)
        _seal_selection(multi)
        result = finalize_native_v60_model(
            candidates, single, multi, self.X, self.y, variable_names=["x"]
        )
        self.assertEqual(result["execution_status"], "selected")
        self.assertEqual(result["selected_model"]["family"], "single_basis")
        self.assertEqual(result["rejected_candidate_options"][0]["reason"], "rank_deficient_training_design")


if __name__ == "__main__":
    unittest.main()
