from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_exp1_llm_sensitivity_is_wired_to_both_canonical_launchers():
    workflow = (ROOT / '.github/workflows/ci_runner_repro.yml').read_text()
    launcher = (ROOT / 'run_all.sh').read_text()
    assert '- exp1_llm_sens' in workflow
    assert 'exp1_llm_sens' in workflow.split('VALID_IDS=', 1)[1].splitlines()[0]
    assert '            exp1_llm_sens)' in workflow
    assert '"exp1_llm_sens":      6' in workflow
    assert '"exp1_llm_sens":     ["pysr_only__na", "hypatia_nollm__na", "pure_llm__named", "pure_llm__neutral", "hypatia__named", "hypatia__neutral"]' in workflow
    assert 'LLM_SENS_RUNNER: "llm_sens_adapter:run"' in workflow
    assert 'LLM_SENS_PRIOR_TARGETS: "hypatia:get_llm_prior"' in workflow
    assert 'LLM_SENS_HOOKS: "hypatia_llm_hook:hybrid_llm_condition"' in workflow
    assert 'exp1_llm_sens' in launcher.split('_STEP_ORDER=', 1)[1].splitlines()[0]
    assert 'run exp1_llm_sens ' in launcher
    assert 'exactly one condition per shard' in launcher
    assert "IFS=', ' read -r -a seed_args" in launcher


def test_exp1_llm_sensitivity_driver_and_adapter_contract_exist():
    bench = ROOT / 'hypatiax/experiments/benchmarks'
    driver = (bench / 'exp1_llm_sens.py').read_text()
    adapter = (bench / 'llm_sens_adapter.py').read_text()
    hook = (bench / 'hypatia_llm_hook.py').read_text()
    assert 'p.add_argument("--runner"' in driver
    assert 'p.add_argument("--only"' in driver
    assert 'def run(cases, case_ids, arm, seed, condition, out_dir):' in adapter
    assert 'def hybrid_llm_condition(' in hook
