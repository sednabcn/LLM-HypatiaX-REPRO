"""Audit C4/L52: exp1_ablation must key engine metadata by the sanitised names
and record llm provenance. Static + behavioural, no engine/API needed."""
import ast, pathlib, re

SRC = pathlib.Path(__file__).resolve().parents[1] / "benchmarks" / "exp1_ablation.py"


def _text():
    return SRC.read_text(encoding="utf-8", errors="replace")


def _sanitizer_cls():
    tree = ast.parse(_text())
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "VariableNameSanitizer")
    ns = {"re": re}
    exec(compile(ast.Module([node], []), str(SRC), "exec"), ns)
    return ns["VariableNameSanitizer"]


def test_reserved_names_are_renamed_and_restored():
    san = _sanitizer_cls()()
    safe, conflict = san.sanitize(["S", "N", "T"])
    assert conflict and safe == ["var_S", "var_N", "T"]
    assert san.restore("var_S/(var_N+T)") == "S/(N+T)"


def test_metadata_keyed_by_safe_names():
    t = _text()
    assert re.search(r'"variable_descriptions":\s*\{sv: ov for sv, ov in zip\(safe_var_names, eq\["vars"\]\)\}', t)
    assert re.search(r'"variable_units":\s*\{sv: "" for sv in safe_var_names\}', t)
    assert '{v: v for v in eq["vars"]}' not in t


def test_rows_record_provenance():
    t = _text()
    for key in ('"llm_source"', '"llm_enabled"', '"llm_model"', '"llm_temperature"', '"sanitized_vars"'):
        assert key in t
    assert "llm_temperature         = LLM_TEMPERATURE" in t


def test_budgets_recorded_per_row():
    t = _text()
    assert t.count('"wall_clock_budget_s"') >= 2 and t.count('"pysr_attempts_allowed"') >= 2


def test_extract_eval_is_decision_aware():
    """Audit L35: a failed llm row must not inherit nn_result's r2 (and vice versa)."""
    base = SRC.parent
    for name in ("run_comparative_suite_benchmark_v2.py", "run_comparative_suite_benchmark_pca.py"):
        t = (base / name).read_text(encoding="utf-8", errors="replace")
        assert "for _key in _eval_keys:" in t
        assert '_eval_keys = ("evaluation", "llm_result", "result")' in t
        assert '_eval_keys = ("evaluation", "nn_result", "result")' in t
        assert 'for _key in ("evaluation", "nn_result", "llm_result", "result"):' not in t


def test_single_temperature_setting_is_wired():
    """Audit C1: 0.25 is set once per entry point and read from LLM_TEMPERATURE."""
    root = SRC.parents[3]
    wf = (root / ".github/workflows/ci_runner_repro.yml").read_text(encoding="utf-8", errors="replace")
    assert 'LLM_TEMPERATURE:  "0.25"' in wf and 'LLM_MODEL:        "claude-sonnet-4-6"' in wf
    sh = (root / "run_all.sh").read_text(encoding="utf-8", errors="replace")
    assert 'export LLM_TEMPERATURE="${LLM_TEMPERATURE:-0.25}"' in sh
    assert "--temperature 0.25" not in sh and sh.count("LLM_TEMPERATURE:-0.25") >= 3
    assert re.search(r"^llm_temperature:\s*0\.25", (root / "config/repro.yaml").read_text(encoding="utf-8"), re.M)
    for rel in ("hypatiax/tools/symbolic/symbolic_engine.py", "hypatiax/tools/symbolic/hybrid_system_v50_2.py"):
        assert 'os.environ.get("LLM_TEMPERATURE"' in (root / rel).read_text(encoding="utf-8", errors="replace")
