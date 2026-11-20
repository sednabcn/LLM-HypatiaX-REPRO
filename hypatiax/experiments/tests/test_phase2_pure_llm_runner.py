"""Offline regression coverage for the Phase 2 Pure-LLM runner contract."""
from pathlib import Path
import json
import subprocess
import sys


REPO = Path(__file__).resolve().parents[3]


def test_phase2_runner_default_inputs_exist():
    assert (REPO / "config" / "phase2_pure_llm_config.yaml").is_file()
    assert (REPO / "config" / "phase2_row_schema.json").is_file()
    assert (REPO / "scripts" / "run_pure_llm_arm.py").is_file()


def test_phase2_runner_offline_selftest():
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_pure_llm_arm.py"), "--selftest"],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "SELFTEST PASSED" in result.stdout


def test_phase2_production_path_uses_hard_process_deadline():
    source = (REPO / "scripts" / "run_pure_llm_arm.py").read_text()
    assert "def run_case_hard(" in source
    assert "timeout=rt.time_cap_s" in source
    assert "run_case_hard(adapter.build(eq, seed)" in source
    assert "row[\"r2\"] = None" in source or '\"r2\": None' in source


def test_phase2_runner_blocks_live_calls_when_prompt_leak_gate_fails():
    source = (REPO / "scripts" / "run_pure_llm_arm.py").read_text()
    assert "render_provider = BaselineProvider(args.baseline, render=True)" in source
    assert "gate_prompt_leaks(rendered_text, preflight_case," in source
    assert "Prompt parity/leak gate failed: no Phase 2 API calls were made." in source


def test_phase2_runner_uses_scored_and_raw_r2_paths():
    source = (REPO / "scripts" / "run_pure_llm_arm.py").read_text()
    assert "return mod.r2_scored" in source
    assert "mod.r2_scored._raw_scorer = mod.r2_checked" in source


def test_phase2_prompt_uses_hds_training_patterns_and_rounded_constants():
    runner = (REPO / "scripts" / "run_pure_llm_arm.py").read_text()
    baseline = (REPO / "hypatiax" / "core" / "base_pure_llm" /
                "baseline_pure_llm_defi_discovery.py").read_text()
    config = (REPO / "config" / "phase2_pure_llm_config.yaml").read_text()
    assert "DataPatternAnalyzer().analyze(case.X_train, case.y_train, case.variable_names)" in runner
    assert '"data_patterns": patterns' in runner
    assert "training_pattern_statistics" in config
    assert "hds_rounded_constants" in config
    assert "DATA PATTERNS (computed from training split only)" in baseline
    assert 'json.dumps(metadata["data_patterns"], indent=2)' in baseline
    assert "NEUTRAL_TASK_DESCRIPTION" in runner
    assert "Prompt parity/leak gate failed: no Phase 2 API calls were made." in runner


def test_phase2_runner_checks_exact_hds_pattern_and_constant_payloads():
    runner = (REPO / "scripts" / "run_pure_llm_arm.py").read_text()
    assert "exact HDS training-pattern payload present" in runner
    assert "exact HDS rounded constants present" in runner
    assert "no training-data statistic values in prompt" not in runner


def test_phase2_rendered_prompt_matches_hds_training_payload_for_fixture():
    import numpy as np
    from hypatiax.tools.symbolic.symbolic_engine import DataPatternAnalyzer
    from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import PureLLMBaseline
    from scripts.run_pure_llm_arm import Case, hds_prompt_context, NEUTRAL_TASK_DESCRIPTION
    from scripts.p2_data import HDS_PROMPT_CONSTANTS

    X = np.column_stack([np.linspace(1.0, 2.0, 40), np.linspace(2.0, 4.0, 40)])
    y = 3.0 * X[:, 0] + 0.5 * X[:, 1] ** 2
    case = Case("Fixture Equation", 42, "Fixture Equation description", "physics",
                ["T", "V"], {}, X, y)
    patterns, constants = hds_prompt_context(case)
    expected = DataPatternAnalyzer().analyze(X, y, ["T", "V"])
    assert patterns == expected
    assert constants == HDS_PROMPT_CONSTANTS

    baseline = object.__new__(PureLLMBaseline)
    prompt = baseline._generate_standard_prompt(
        NEUTRAL_TASK_DESCRIPTION, case.domain, case.variable_names,
        {"constants": constants, "data_patterns": patterns})
    assert json.dumps(expected, indent=2) in prompt
    assert "Fixture Equation" not in prompt
    assert "Fixture Equation description" not in prompt
    assert NEUTRAL_TASK_DESCRIPTION in prompt
    assert "h=6.626e-34 (Planck)" in prompt
    assert "Do NOT use bare 'e' for elementary charge — use q_e instead." in prompt
