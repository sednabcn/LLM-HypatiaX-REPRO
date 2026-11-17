"""The Exp2 Feynman runners must use one canonical extrapolation implementation."""
import ast
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1] / "benchmarks"
CORE = BENCH / "exp2_extrapolation_core.py"
RUNNERS = (
    BENCH / "extrap_r2_far.py",
    BENCH / "run_comparative_suite_benchmark_v2.py",
    BENCH / "run_comparative_suite_benchmark_pca.py",
)
FUNCTIONS = (
    "calculate_extrapolation_error",
    "extrapolation_error_status",
    "build_extrap_split",
    "_runner_eval_formula",
    "_far_r2",
    "_far_rmse",
    "compute_extrap_r2_far",
)


def _top_level_functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_shared_core_owns_each_extrapolation_helper_once():
    functions = _top_level_functions(CORE)
    for name in FUNCTIONS:
        assert name in functions
    for runner in RUNNERS:
        tree = ast.parse(runner.read_text(encoding="utf-8"))
        runner_functions = {
            node.name for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        runner_classes = {
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        }
        assert not (set(FUNCTIONS) & runner_functions), (
            f"{runner.name} still contains duplicated extrapolation helpers"
        )
        assert "ExtrapolationRegime" not in runner_classes
        source = runner.read_text(encoding="utf-8")
        assert "from hypatiax.experiments.benchmarks.exp2_extrapolation_core import" in source


def test_far_r2_uses_canonical_scorer():
    tree = ast.parse(CORE.read_text(encoding="utf-8"))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_far_r2")
    source = ast.unparse(fn)
    assert "_r2_scored" in source
    assert "ss_tot" not in source and "ss_res" not in source


def test_shared_core_has_no_experiment_or_optional_backend_imports():
    tree = ast.parse(CORE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not ({"torch", "anthropic", "juliacall", "random", "os"} & imported)
