"""B2/B3: M4 rows must carry the hybrid's formula (nested under llm_result)."""
import ast, pathlib, textwrap

SRC = pathlib.Path(__file__).resolve().parents[1] / "benchmarks/run_comparative_suite_benchmark_v2.py"


def _load():
    tree = ast.parse(SRC.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_extract_formula")
    ns = {}
    exec(compile(ast.Module([fn], []), "x", "exec"), ns)
    return ns["_extract_formula"]


def test_nested_formula_found():
    f = _load()
    assert f({"llm_result": {"formula": "a*b"}}) == "a*b"


def test_top_level_wins_and_na_ignored():
    f = _load()
    assert f({"formula": "x+1", "llm_result": {"formula": "y"}}) == "x+1"
    assert f({"formula": "N/A", "llm_result": {"formula": "z"}}) == "z"


def test_missing_gives_na():
    f = _load()
    assert f({}) == "N/A" and f(None) == "N/A" and f({"llm_result": {"formula": "N/A"}}) == "N/A"
