"""Regression tests for the 4060 predictive-R2 threshold classifier."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ci" / "exp1_4060_seed_outputs.py"
SPEC = importlib.util.spec_from_file_location("exp1_4060_seed_outputs", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def row_with_r2(value):
    return {"results": {"hybrid": {"test_r2": value}}}


class PredictiveR2ClassificationTests(unittest.TestCase):
    def test_threshold_is_a_predictive_pass_not_a_symbolic_claim(self):
        self.assertTrue(MODULE.is_near_perfect_predictive_pass(row_with_r2(0.999999)))

    def test_score_below_threshold_is_not_a_pass(self):
        self.assertFalse(MODULE.is_near_perfect_predictive_pass(row_with_r2(0.9999989)))

    def test_missing_and_nonfinite_scores_are_not_passes(self):
        self.assertFalse(MODULE.is_near_perfect_predictive_pass(row_with_r2(None)))
        self.assertFalse(MODULE.is_near_perfect_predictive_pass(row_with_r2(float("nan"))))

    def test_out_of_range_score_is_not_counted(self):
        self.assertFalse(MODULE.is_near_perfect_predictive_pass(row_with_r2(1.02)))

    def test_custom_threshold_is_respected(self):
        self.assertTrue(
            MODULE.is_near_perfect_predictive_pass(row_with_r2(0.95), threshold=0.9)
        )


if __name__ == "__main__":
    unittest.main()
