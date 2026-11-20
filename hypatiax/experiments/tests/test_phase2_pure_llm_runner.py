"""Offline regression coverage for the Phase 2 Pure-LLM runner contract."""
from pathlib import Path
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
