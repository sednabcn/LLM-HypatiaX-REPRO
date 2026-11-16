"""Offline contracts for the single-call training-summary prompt path."""

import json

import numpy as np

from hypatiax.experiments.benchmarks import run_data_informed_llm_pilot as pilot


def test_compact_stats_are_derived_from_supplied_training_partition():
    X_train = np.asarray([[1.0], [2.0], [3.0], [4.0]])
    y_train = np.asarray([2.0, 4.0, 6.0, 8.0])

    summary = pilot.compact_stats(X_train, y_train, ["M"])

    assert summary["n"] == 4
    assert summary["features"]["M"]["min"] == 1.0
    assert summary["features"]["M"]["max"] == 4.0
    assert summary["features"]["M"]["mean"] == 2.5
    assert summary["features"]["M"]["target_correlation"] == 1.0
    assert summary["target"]["mean"] == 5.0


def test_training_summary_prompt_contains_statistics_not_raw_rows():
    X_train = np.asarray([[1.0], [2.0], [3.0], [4.0]])
    y_train = np.asarray([2.0, 4.0, 6.0, 8.0])
    eq = {"name": "Allometric Scaling", "domain": "biology"}
    names = ["M"]

    summary = pilot.compact_stats(X_train, y_train, names)
    prompt = pilot.prompt_for(
        eq, names, "training_summary_statistics",
        X_train, y_train, examples=[],
    )

    assert "Training-only summary statistics (no raw rows)" in prompt
    assert json.dumps(summary, sort_keys=True) in prompt
    assert "def formula(M):" in prompt
    assert "Do not mention or request test or extrapolation data." in prompt
    assert "Training-only input/output examples" not in prompt
    assert "ground_truth" not in prompt.lower()
