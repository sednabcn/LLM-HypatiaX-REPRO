"""hypatiax.core.metrics must keep its public API *and* use the canonical R^2 policy.

Regression: a replacement of core/metrics.py once dropped compute_r2 & friends and
broke ``from hypatiax.core.metrics import compute_r2`` in the ensemble module
(only noticed when pytest failed at collection).
"""
import ast
import math
import pathlib

import numpy as np
import pytest

from hypatiax.core import metrics as M
from hypatiax.core.r2_canonical import r2_checked

ROOT = pathlib.Path(__file__).resolve().parents[3]

PUBLIC_API = [
    "compute_r2", "compute_mse", "compute_rmse", "compute_mae", "compute_max_error",
    "compute_near_perfect_rate", "compute_exact_recovery_rate", "compute_catastrophic_rate",
    "compute_speedup", "evaluate_all",
    "r2_checked", "r2", "r2_scored", "is_recovered", "selection_score",
]


@pytest.mark.parametrize("name", PUBLIC_API)
def test_public_api_present(name):
    assert callable(getattr(M, name))


def test_every_importer_of_core_metrics_finds_its_names():
    """Static check: any `from hypatiax.core.metrics import X` in the repo resolves."""
    missing = []
    for path in (ROOT / "hypatiax").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "hypatiax.core.metrics":
                for a in node.names:
                    if not hasattr(M, a.name):
                        missing.append(f"{path.relative_to(ROOT)}: {a.name}")
    assert not missing, "names imported from hypatiax.core.metrics but not defined:\n  " + "\n  ".join(missing)


def test_compute_r2_follows_canonical_policy():
    y = np.linspace(1.0, 2.0, 40)
    assert M.compute_r2(y, y) == pytest.approx(1.0)
    assert M.compute_r2(y, y) == r2_checked(y, y)[0]
    assert math.isnan(M.compute_r2([5, 5, 5], [5, 5, 5]))            # constant target: undefined, not 1.0
    assert math.isnan(M.compute_r2([5, 5, 5], [9, 9, 9]))            # ... and not 0.0
    assert M.compute_r2(y, np.where(np.arange(40) == 3, np.nan, y)) == float("-inf")   # failed prediction
    t = np.linspace(1.0, 2.0, 40) * 1e-11                             # tiny scale is scored, not collapsed
    assert M.compute_r2(t, t * 1.5) < 0.5


def test_compute_r2_input_contract_kept():
    with pytest.raises(ValueError):
        M.compute_r2([1, np.nan, 3], [1, 2, 3])                       # non-finite y_true is a data bug
    with pytest.raises(ValueError):
        M.compute_r2([1, 2, 3], [1, 2])                               # length mismatch
    with pytest.raises(ValueError):
        M.compute_r2([], [])


def test_rates_count_failures():
    scores = [0.995, float("nan"), float("-inf"), -3.0, 0.5]
    assert M.compute_catastrophic_rate(scores) == pytest.approx(3 / 5)   # nan, -inf, -3.0
    assert M.compute_near_perfect_rate(scores) == pytest.approx(1 / 5)
