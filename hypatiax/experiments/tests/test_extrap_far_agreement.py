"""L45: the three copies of compute_extrap_r2_far (and its scoring helpers) must stay identical.

Compared on the AST (comments, docstrings and formatting ignored) and without importing the
runners, so the test needs neither torch nor an API key. If one copy is edited, edit all three
(or consolidate them on extrap_r2_far.py) -- otherwise this test fails.
"""
import ast
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[1] / "benchmarks"
FILES = {
    "extrap_r2_far": BENCH / "extrap_r2_far.py",
    "v2": BENCH / "run_comparative_suite_benchmark_v2.py",
    "pca": BENCH / "run_comparative_suite_benchmark_pca.py",
}
FUNCS = ("compute_extrap_r2_far", "_far_r2", "_far_rmse")


def _norm(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(fns) == 1, f"{path.name}: expected exactly one top-level def {name}, found {len(fns)}"
    fn = fns[0]
    if ast.get_docstring(fn):
        fn.body = fn.body[1:]
    return ast.unparse(fn)


@pytest.mark.parametrize("name", FUNCS)
@pytest.mark.parametrize("other", ["v2", "pca"])
def test_copies_agree(name, other):
    ref = _norm(FILES["extrap_r2_far"], name)
    assert _norm(FILES[other], name) == ref, (
        f"{name} in {FILES[other].name} differs from extrap_r2_far.py; "
        "sync the copies or consolidate them (ledger L45)"
    )


@pytest.mark.parametrize("key", FILES)
def test_far_r2_uses_canonical_scorer(key):
    """No copy may re-implement R^2: _far_r2 must delegate to r2_canonical.r2_scored."""
    src = _norm(FILES[key], "_far_r2")
    assert "_r2_scored" in src
    assert "ss_tot" not in src and "ss_res" not in src
