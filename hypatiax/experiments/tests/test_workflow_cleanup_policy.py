"""Regression checks for the conservative workflow-run retention policy."""
from pathlib import Path
import re

WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "clean-old-workflows.yml"


def _source():
    return WORKFLOW.read_text(encoding="utf-8")


def _preservation_policy():
    source = _source()
    ids_match = re.search(r"PRESERVED_WORKFLOW_IDS\s*=\s*new Set\(\[([^]]*)\]\)", source)
    assert ids_match, "preserved workflow ID set is missing"
    workflow_ids = {int(value) for value in re.findall(r"\d+", ids_match.group(1))}
    patterns_match = re.search(r"PRESERVED_WORKFLOW_NAME_PATTERNS\s*=\s*\[(.*?)\]", source, re.DOTALL)
    assert patterns_match, "preserved workflow name patterns are missing"
    patterns = re.findall(r"/((?:\\.|[^/])*)/i", patterns_match.group(1))
    return workflow_ids, [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def test_known_experiment_and_repro_workflow_ids_are_preserved():
    workflow_ids, _ = _preservation_policy()
    assert {400368487, 315086159}.issubset(workflow_ids)


def test_phase_three_ablation_name_variants_are_preserved():
    _, patterns = _preservation_policy()
    for name in ("Phase 3 ablation", "phase3 ablation results"):
        assert any(pattern.search(name) for pattern in patterns), name


def test_runner_reproduction_name_variants_are_preserved():
    _, patterns = _preservation_policy()
    for name in ("Runner reproduction, exp1 ablation", "runner-repro", "repro runner"):
        assert any(pattern.search(name) for pattern in patterns), name


def test_deletion_gate_remains_conservative():
    source = _source()
    assert "if (oldEnough && successful && !protectedBranch && !protectedWorkflow) runsToDelete.push(run);" in source
    assert "run.status === 'completed' && run.conclusion === 'success'" in source
    assert "PROTECTED_BRANCHES.has(run.head_branch)" in source
