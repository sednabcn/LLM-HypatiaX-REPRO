"""Offline contract tests for the five-seed Core-15 gatherer."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/ci/gather_ablation_seeds.py"
SPEC = importlib.util.spec_from_file_location("gather_ablation_seeds", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_seed(root: Path, seed: int):
    directory = MODULE.seed_dir(root, seed)
    directory.mkdir(parents=True, exist_ok=True)
    results = {}
    for eq_id in range(15):
        equation = {"name": f"Equation {eq_id}", "domain": "Test"}
        for arm in MODULE.ARMS:
            equation[arm] = {
                "condition": arm,
                "completed": True,
                "success": True,
                "fit_status": "success",
                "evaluation_status": "success",
                "test_r2": 0.99,
                "extrap_r2_far": 0.98,
            }
        results[str(eq_id)] = equation
    (directory / "exp1_ablation_results.json").write_text(json.dumps(results))
    (directory / "exp1_rf01_mannwhitney.json").write_text("{}")
    (directory / "exp1_llm_contribution.json").write_text("{}")
    provenance = {
        "seed": seed,
        "source_revision": "deadbeef",
        "benchmark_script_sha256": "a" * 64,
        "engine_version": "5.4",
        "populations": 30,
        "niterations": 1000,
        "model_string": "test-model",
        "flags": {"clean_run": True},
    }
    (directory / "provenance_map_exp1.json").write_text(json.dumps(provenance))
    return directory


def _write_all(root: Path):
    for seed in MODULE.CANONICAL_SEEDS:
        _write_seed(root, seed)


def test_gatherer_requires_exact_canonical_seed_order():
    assert MODULE.parse_seeds("42,99,123,777,2024") == list(MODULE.CANONICAL_SEEDS)
    for raw in ("42,99,123,777", "42,99,123,777,2025", "99,42,123,777,2024"):
        try:
            MODULE.parse_seeds(raw)
        except SystemExit as exc:
            assert "fixed to" in str(exc)
        else:
            raise AssertionError(f"noncanonical seed list accepted: {raw}")


def test_gatherer_validates_all_fifteen_equations_and_three_terminal_arms(tmp_path):
    _write_all(tmp_path)
    manifest_path = tmp_path / MODULE.OUT_SUBDIR / MODULE.MANIFEST_NAME
    status = MODULE.main([
        "--results-root", str(tmp_path),
        "--seeds", "42,99,123,777,2024",
    ])
    assert status == 0
    manifest = json.loads(manifest_path.read_text())
    assert manifest["all_complete"] is True
    assert manifest["expected_equations"] == 15
    assert manifest["expected_arms"] == list(MODULE.ARMS)
    assert all(item["status"] == "complete" for item in manifest["per_seed"].values())


def test_gatherer_writes_diagnostic_manifest_for_incomplete_arm(tmp_path):
    _write_all(tmp_path)
    results_path = MODULE.seed_dir(tmp_path, 123) / "exp1_ablation_results.json"
    results = json.loads(results_path.read_text())
    results["4"]["hypatia_nollm"]["completed"] = False
    results_path.write_text(json.dumps(results))

    status = MODULE.main([
        "--results-root", str(tmp_path),
        "--seeds", "42,99,123,777,2024",
    ])
    manifest = json.loads((tmp_path / MODULE.OUT_SUBDIR / MODULE.MANIFEST_NAME).read_text())
    assert status == 1
    assert manifest["all_complete"] is False
    assert manifest["per_seed"]["123"]["status"] == "incomplete"
    assert any("not terminal" in problem for problem in manifest["per_seed"]["123"]["problems"])


def test_gatherer_detects_cross_seed_source_and_protocol_mismatch(tmp_path):
    _write_all(tmp_path)
    provenance_path = MODULE.seed_dir(tmp_path, 2024) / "provenance_map_exp1.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["source_revision"] = "different-revision"
    provenance_path.write_text(json.dumps(provenance))

    entries = {
        str(seed): MODULE.gather_seed(tmp_path, seed)
        for seed in MODULE.CANONICAL_SEEDS
    }
    problems = MODULE.cross_seed_problems(entries, MODULE.CANONICAL_SEEDS)
    assert any("source_revision" in problem for problem in problems)


def test_gatherer_rejects_bad_run_map_entries():
    for raw in ("42", "42:not-a-run", "7:1234", "42:1234,42:5678"):
        try:
            MODULE.parse_run_map(raw)
        except SystemExit:
            pass
        else:
            raise AssertionError(f"invalid run map accepted: {raw}")


def test_workflow_enforces_fixed_seeds_and_gathers_failed_run_diagnostics():
    workflow = (ROOT / ".github/workflows/ci_runner_repro.yml").read_text()
    assert 'CANONICAL_SEEDS="42,99,123,777,2024"' in workflow
    assert "steps.dispatch.outputs.state == 'failed'" in workflow
    assert "DISPATCH_STATE: ${{ steps.dispatch.outputs.state }}" in workflow
    assert "Gathering diagnostics before returning failure." in workflow
    assert "GATHER_STATUS=$?" in workflow
    assert 'git add -f "${ROOT}/exp1_ablation_seeds"' in workflow


def test_workflow_runs_descriptive_aggregator_only_after_valid_gather():
    workflow = (ROOT / ".github/workflows/ci_runner_repro.yml").read_text()
    gather = workflow.split("- name: Gather per-seed results", 1)[1].split(
        "  pca_runner:", 1
    )[0]
    assert 'if [[ "${GATHER_STATUS}" -eq 0 ]]' in gather
    assert "scripts/ci/aggregate_exp1_ablation_multiseed.py --results-root" in gather
    assert 'git add -f "${ROOT}/exp1_ablation_multiseed"' in gather
    assert '"${DISPATCH_STATE}" == "failed"' in gather


def test_dispatch_run_lookup_is_correlated_with_the_requested_seed():
    workflow = (ROOT / ".github/workflows/ci_runner_repro.yml").read_text()
    assert "format(' · seed={0}', inputs.seeds || '42')" in workflow
    assert '--arg seed "${SEED}"' in workflow
    assert 'test("seed=" + $seed; "i")' in workflow
