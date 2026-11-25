"""Regression contracts for the Core-15 Exp1 ablation runner.

These tests are intentionally offline: they exercise deterministic data and
statistical helpers, and statically verify the CI completion contract. They
must not launch PySR or call an LLM provider.
"""
import ast
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "hypatiax/experiments/benchmarks/exp1_ablation.py"
RUNNER_PATH = ROOT / "run_all.sh"
WORKFLOW_PATH = ROOT / ".github/workflows/ci_runner_repro.yml"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")


def _load_source_function(name):
    tree = ast.parse(SOURCE)
    node = next(
        item for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
    )
    isolated = ast.Module(body=[node], type_ignores=[])
    namespace = {"np": np}
    exec(compile(isolated, str(SOURCE_PATH), "exec"), namespace)
    return namespace[name]


def test_hybrid_discover_receives_equation_specific_seed():
    assert '"random_seed":             eq_seed' in SOURCE
    assert SOURCE.index('"random_seed":             eq_seed') < SOURCE.index('res = hybrid.discover(')


def test_portfolio_ood_rho_remains_a_valid_correlation():
    generator = _load_source_function("generate_extrap_data")
    eq = {
        "name": "Portfolio Std Dev",
        "vars": ["s1", "s2", "rho"],
        "train_range": [(0.01, 0.2), (0.01, 0.2), (-0.8, 0.8)],
        "extrap_range": [(0.2, 0.5), (0.2, 0.5), (-0.9, 0.9)],
        "extrapolation_ranges": {
            "near": [(0.2, 0.3), (0.2, 0.3), (-0.9, 0.9)],
            "far": [(0.8, 1.2), (0.8, 1.2), (-0.99, 0.99)],
        },
        "fn": lambda s1, s2, rho: np.sqrt(s1**2 + s2**2 + 2 * rho * s1 * s2),
    }
    for regime in ("near", "far"):
        X, y = generator(eq, regime=regime, N=128, seed=777, domain_validated=True)
        assert np.all(np.abs(X[:, 2]) <= 1.0)
        assert np.all(np.isfinite(y))
    assert np.all((generator(eq, "far", N=128, seed=777, domain_validated=True)[0][:, :2]) > 0.2)


def test_pysr_evaluation_failure_is_not_marked_successful():
    assert '"evaluation_status":     "success" if (_evaluation_error is None and _primary_eval_ok) else "failed"' in SOURCE
    assert '"success":               bool(_evaluation_error is None and _primary_eval_ok)' in SOURCE
    assert '"completed":' in SOURCE


def test_terminal_failure_is_distinct_from_missing_work():
    assert '"fit_status":           "timeout"' in SOURCE
    assert '"fit_status":           "error"' in SOURCE
    assert '"evaluation_status":    "not_run"' in SOURCE
    assert 'entry[c].get("completed") is True' in SOURCE


def test_rf01_effect_size_is_paired_signed_rank():
    helper = _load_source_function("_paired_rank_biserial")
    assert helper([1.0, 2.0, 3.0]) == 1.0
    assert helper([-1.0, -2.0, -3.0]) == -1.0
    assert helper([0.0, 0.0]) == 0.0
    assert '"rank_biserial_method": "paired_signed_rank"' in SOURCE
    assert '"wilcoxon_unavailable"' in SOURCE
    assert "else float(p_gt)" not in SOURCE


def test_ci_requires_terminal_records_and_preserves_tables():
    runner = RUNNER_PATH.read_text(encoding="utf-8")
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert 'v[a].get("completed") is not True' in runner
    assert 'v[a].get("completed") is not True' in workflow
    assert "retained ${ntex} generated .tex table artifact(s)" in runner
    assert "find \"${abl_dir}\" -maxdepth 1 -name '*.tex' -delete" not in runner


def test_portfolio_seed_sweep_is_explicit_not_implicit_readiness_blocker():
    assert "optional diagnostic not run" in SOURCE
    assert 'checks.append(("C4 Portfolio seed sweep"' not in SOURCE
    assert 'parser.add_argument("--seed-sweep"' in SOURCE
