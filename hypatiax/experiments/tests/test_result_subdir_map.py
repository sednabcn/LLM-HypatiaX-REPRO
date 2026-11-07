from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / ".github" / "scripts" / "result_subdir_map.py"
SPEC = importlib.util.spec_from_file_location("result_subdir_map", MODULE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_exp1b_uses_the_canonical_deFi_benchmark_directory():
    assert mod.resolve_result_subdir("exp1b") == (
        "comparison_results/noise-noiseless/15"
    )


def test_exp1b_pca_uses_the_pca_portfolio_directory():
    assert mod.resolve_result_subdir("exp1b_pca") == (
        "comparison_results/noise-noiseless/15_pca"
    )


def test_noise_sweep_maps_to_single_canonical_directory():
    assert mod.resolve_result_subdir("suppB") == (
        "comparison_results/feynman-tests/noise-sweep"
    )


def test_unknown_experiment_does_not_guess_a_directory():
    assert mod.resolve_result_subdir("not-an-experiment") == ""
