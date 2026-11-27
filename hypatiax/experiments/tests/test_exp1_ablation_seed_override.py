"""Regression tests for exp1_ablation's explicit multi-seed contract."""

from pathlib import Path
import subprocess


def test_exp1_ablation_allows_requested_seed_without_weakening_other_protocols():
    repo_root = Path(__file__).resolve().parents[3]
    run_all = (repo_root / "run_all.sh").read_text(encoding="utf-8")
    workflow = (repo_root / ".github/workflows/ci_runner_repro.yml").read_text(
        encoding="utf-8"
    )

    # The runner marks exp1_ablation workers and supplies the selected seed.
    assert 'EXP1_ABLATION_SEED_IN_DIR: "1"' in workflow
    assert '[[ "${EXP1_ABLATION_SEED_IN_DIR:-0}" == "1" || -n "${ABLATION_SUBDIR:-}" ]]' in run_all

    # Only ablation runs bypass the fixed YAML default-seed check.
    assert 'check_protocol_override PYSR_SEED "$_CFG_PYSR_SEED"' in run_all
    assert 'check_protocol_override HYPATIAX_ENGINE_SEED "$_CFG_PYSR_SEED"' in run_all
    assert 'export HYPATIAX_ENGINE_SEED="$PYSR_SEED"' in run_all
    assert 'export PYSR_SEED="$_CFG_PYSR_SEED"' in run_all

    # Seed 42 remains the default; supplied numeric seeds are preserved and
    # malformed seeds or inconsistent engine seeds are rejected.
    assert 'export PYSR_SEED="${PYSR_SEED:-42}"' in run_all
    assert 'PYSR_SEED:-' in run_all
    assert 'must match exp1_ablation PYSR_SEED' in run_all

    checked = subprocess.run(
        ["bash", "-n", str(repo_root / "run_all.sh")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr
