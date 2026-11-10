"""Regression tests for mutually exclusive DeFi benchmark dispatch routes."""

from pathlib import Path
import subprocess


WORKFLOW = (
    Path(__file__).resolve().parents[3]
    / ".github"
    / "workflows"
    / "ci_runner_repro.yml"
)


def _run_duplicate_guard(ids: str) -> subprocess.CompletedProcess[str]:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    marker = "          HAS_PROVENANCE=false\n"
    assert marker in workflow, "workflow duplicate-dispatch guard is missing"
    guard = workflow.split(marker, 1)[1].split(
        '\n          echo "::notice::Fanning out', 1
    )[0]
    script = 'IDS="$1"\n' + marker + guard + '\necho ACCEPTED\n'
    return subprocess.run(
        ["bash", "-c", script, "bash", ids],
        check=False,
        capture_output=True,
        text=True,
    )


def test_standalone_five_seed_provenance_route_is_allowed() -> None:
    result = _run_duplicate_guard("exp1-provenance")
    assert result.returncode == 0, result.stderr
    assert "ACCEPTED" in result.stdout


def test_split_seed_route_is_allowed_without_provenance_route() -> None:
    result = _run_duplicate_guard("exp1 exp1b_seeds")
    assert result.returncode == 0, result.stderr
    assert "ACCEPTED" in result.stdout


def test_provenance_route_cannot_repeat_seed_42_baseline() -> None:
    result = _run_duplicate_guard("exp1-provenance exp1")
    assert result.returncode != 0
    assert "Duplicate DeFi benchmark dispatch" in result.stderr


def test_provenance_route_cannot_repeat_other_four_seeds() -> None:
    result = _run_duplicate_guard("exp1-provenance exp1b_seeds")
    assert result.returncode != 0
    assert "Duplicate DeFi benchmark dispatch" in result.stderr
