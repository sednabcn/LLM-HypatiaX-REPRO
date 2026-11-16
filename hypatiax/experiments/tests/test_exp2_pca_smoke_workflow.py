"""Offline CI contract tests for the bounded Exp2 PCA smoke workflow.

These tests deliberately do not import the experiment runner or initialize Julia,
PySR, Torch, or an LLM client. They protect the dispatch/validation contract.
"""
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "exp2_pca_smoke.yml"
RUNNER_PATH = ROOT / "hypatiax" / "experiments" / "benchmarks" / "run_comparative_suite_benchmark_pca.py"


def _workflow():
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_exp2_pca_smoke_is_manual_and_caps_selection_at_three():
    workflow = _workflow()
    triggers = workflow.get("on", workflow.get(True, {}))
    assert set(triggers) == {"workflow_dispatch"}
    selection = triggers["workflow_dispatch"]["inputs"]["equation_ids"]
    assert selection["required"] is True
    assert "1 2 3" in selection["default"]
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "1 <= len(tokens) <= 3" in source
    assert "len(set(tokens)) != len(tokens)" in source
    assert "re.fullmatch" in source


def test_exp2_pca_smoke_runs_only_corrected_methods_and_fresh_pca_protocol():
    workflow = _workflow()
    job = workflow["jobs"]["pca_smoke"]
    assert job["timeout-minutes"] <= 180
    env = job["env"]
    assert env["HYPATIAX_STRICT"] == "1"
    assert env["HYPATIAX_DISABLE_HARDCODED"] == "1"
    assert env["HYPATIAX_DISABLE_PROMPT_HINTS"] == "1"
    assert env["HYPATIAX_R2_SIGN_FLIP"] == "0"

    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "--benchmark feynman" in source
    assert "--noiseless" in source
    assert "--threshold 0.999999" in source
    assert "--methods 3 6" in source
    assert "--no-llm-cache" in source
    assert "--force-fresh" in source
    assert "--no-checkpoint" in source
    assert "pca_40_60" in source
    assert "pca_test_r2" in source
    assert "external_holdout_status" in source
    assert "score < threshold" in source


def test_exp2_pca_smoke_checks_exact_equation_identity_and_uploads_diagnostics():
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "expected_descriptions" in source
    assert "actual_descriptions" in source
    assert "actual_descriptions != expected_descriptions" in source
    assert "actions/upload-artifact@" in source
    assert "if: always()" in source
    assert "retention-days: 30" in source


def test_exp2_pca_runner_exposes_equation_selection_and_holdout_export():
    runner = RUNNER_PATH.read_text(encoding="utf-8")
    assert 'dest="equations"' in runner
    assert "_equation_indices" in runner
    assert 'record["pca_test_r2"]' in runner
    assert 'record["pca_split_protocol"]' in runner
