from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / ".github" / "workflows" / "ci_runner_repro.yml"
QUALIFIER = ROOT / ".github" / "workflows" / "ci_pipeline_check.yml"


def test_exp2_extrap_worker_generates_and_verifies_discovery_report_sidecar():
    workflow = RUNNER.read_text(encoding="utf-8")
    assert "scripts/ci/validate_exp2_extrap_worker.py" in workflow
    assert '--output-dir "${TARGET}"' in workflow
    assert '--run-start-marker "${RUN_START_MARKER}"' in workflow
    assert "discovery_reports_extrap.json" in workflow
    assert "discovery_report_artifact" in workflow
    assert "sha256" in workflow
    assert "no_typed_discovery_reports" in workflow
    assert "Validated durable discovery report sidecar" in workflow


def test_exp2_extrap_sidecar_is_in_both_pipeline_qualification_tables():
    workflow = QUALIFIER.read_text(encoding="utf-8")
    assert workflow.count('"exp2_feynman_extrap": ["benchmark_results_extrap*.json", "protocol_core_extrap_*.json",') == 2
    assert workflow.count('"exp2_extrap_summary.json", "discovery_reports_extrap.json"') == 2


def test_exp2_extrap_upload_captures_the_entire_result_directory():
    workflow = RUNNER.read_text(encoding="utf-8")
    upload = workflow.split("- name: Upload shard results artifact", 1)[1].split("- name:", 1)[0]
    assert "actions/upload-artifact@" in upload
    assert "format('{0}/{1}/', env.OUT_BASE, needs.plan.outputs.result_subdir)" in upload
