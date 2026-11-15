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
    """Audit C1: model/temperature have one protocol source, exported by run_all."""
    root = SRC.parents[3]
    cfg = (root / "config/repro.yaml").read_text(encoding="utf-8", errors="replace")
    assert re.search(r'^llm_model:\s*"claude-sonnet-4-6"\s*$', cfg, re.M)
    assert re.search(r"^llm_temperature:\s*0\.25\s*$", cfg, re.M)

    wf = (root / ".github/workflows/ci_runner_repro.yml").read_text(encoding="utf-8", errors="replace")
    # The workflow must not shadow the protocol values; run_all owns the export.
    assert not re.search(r"^\s*(?:LLM_TEMPERATURE|LLM_MODEL):", wf, re.M)

    sh = (root / "run_all.sh").read_text(encoding="utf-8", errors="replace")
    assert 'check_protocol_override LLM_TEMPERATURE "$_CFG_LLM_TEMPERATURE"' in sh
    assert 'check_protocol_override LLM_MODEL "$_CFG_LLM_MODEL"' in sh
    assert 'export LLM_TEMPERATURE="$_CFG_LLM_TEMPERATURE"' in sh
    assert 'export LLM_MODEL="$_CFG_LLM_MODEL"' in sh
    assert 'cfg.get("llm_temperature", 0.25)' in sh
    assert 'cfg.get("llm_model", "claude-sonnet-4-6")' in sh
    assert "--temperature 0.25" not in sh
    # Runtime call sites must consume the same fixed protocol source;
    # environment overrides are intentionally ignored by the shared wrapper.
    wrapper = (root / "hypatiax/core/llm_call.py").read_text(encoding="utf-8", errors="replace")
    assert "def configured_temperature() -> float:" in wrapper
    assert "return 0.25" in wrapper
    assert 'kwargs = {**kwargs, "temperature": req}' in wrapper
    assert "client.messages.create(**kwargs)" in wrapper
    assert "os.environ.get(\"LLM_TEMPERATURE\"" not in wrapper


def test_no_silent_zero_r2_defaults():
    """Audit L36/L38: a missing r2 must become 'unavailable', never a 0.0 score."""
    base = SRC.parent
    for name in ("run_comparative_suite_benchmark_v2.py", "run_comparative_suite_benchmark_pca.py"):
        t = (base / name).read_text(encoding="utf-8", errors="replace")
        assert not re.search(r'get\("r2",\s*0\.0\)', t), name
        assert "AUDIT L36" in t or 'evaluation has no r2' in t
    assert 'res.get("rmse", float("inf"))' not in _text()



def test_rows_record_raw_extrapolation_and_real_llm_metadata():
    t = _text()
    assert 'from hypatiax.core.r2_canonical import r2_detail as _r2_detail' in t
    assert '"extrap_r2_raw":' in t and '"extrap_r2_status":' in t
    assert 'from hypatiax.core.llm_meta import llm_meta' in t
    assert '"llm_time_s":            _llm_m["llm_time_s"]' in t
    assert '"llm_expression":        _llm_m["llm_expression"]' in t
    assert '"llm_confidence":        _llm_m["llm_confidence"]' in t


def test_total_time_is_wall_clock_and_llm_time_is_a_subset():
    t = _text()
    assert '"total_time_s":          sr_time,  # discover() wall time includes LLM; llm_time_s is a subset.' in t


def test_provenance_detects_untracked_source_and_config_files():
    t = _text()
    assert '"--untracked-files=all"' in t
    assert '":(exclude)hypatiax/data/results"' in t
    assert '"tracked_and_untracked_worktree_excl_data_results"' in t
