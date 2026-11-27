"""Regression tests for the exp1b_pca run_all.sh shell wrapper."""

from pathlib import Path
import re
import subprocess


def test_exp1b_pca_bash_c_payload_is_valid_shell():
    """Catch quoting regressions hidden inside run_all.sh's nested bash -c string."""
    repo_root = Path(__file__).resolve().parents[3]
    run_all = (repo_root / "run_all.sh").read_text(encoding="utf-8")

    start = re.search(r'^run exp1b_pca .* bash -c "\n', run_all, flags=re.MULTILINE)
    assert start is not None, "exp1b_pca run_all.sh step was not found"

    remainder = run_all[start.end() :]
    end = re.search(r'^"\s*$', remainder, flags=re.MULTILINE)
    assert end is not None, "exp1b_pca bash -c payload has no closing delimiter"

    raw_payload = remainder[: end.start()]
    # Decode the escapes applied by the outer bash double-quoted argument.
    payload = re.sub(r'\\(["$\\])', r'\1', raw_payload)
    checked = subprocess.run(
        ["bash", "-n", "-c", payload],
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr



def test_exp1b_pca_skip_guard_requires_all_five_seed_results_and_summaries():
    repo_root = Path(__file__).resolve().parents[3]
    workflow = (repo_root / ".github/workflows/ci_runner_repro.yml").read_text()
    guard = workflow.split("- name: Check if exp1b_pca results already exist", 1)[1].split(
        "- name: Set up Python", 1
    )[0]
    for seed in (42, 99, 123, 777, 2024):
        assert f"hypatiax_defi_benchmark_pca_results_seed{seed}.json" in guard
    assert "split_protocol_disclosure.json" in guard
    assert "exp1b_pca_summary.json" in guard
    assert "MISSING=()" in guard
    assert '[[ ! -s "${FILE}" ]]' in guard



def test_exp1b_pca_runs_each_canonical_seed_in_an_isolated_process():
    repo_root = Path(__file__).resolve().parents[3]
    run_all = (repo_root / "run_all.sh").read_text(encoding="utf-8")
    start = run_all.index('run exp1b_pca "')
    end = run_all.index('\nrun ', start)
    block = run_all[start:end]

    assert "_PCA_SEEDS=(42 99 123 777 2024)" in block
    escaped_quote = chr(92) + chr(34)
    escaped_dollar = chr(92) + "$"
    for variable in ("DEFI_SEEDS", "PYSR_SEED", "EXPERIMENT_SEED", "NN_SEED"):
        assert variable + "=" + escaped_quote + escaped_dollar + "{_SEED}" + escaped_quote in block
    assert "_SEED_SCRATCH=" + escaped_quote + escaped_dollar + "{_PCA_SCRATCH_ROOT}/seed" + escaped_dollar + "{_SEED}" + escaped_quote in block
    for inherited_filter in ("TASK_IDS", "SHARD_IDS", "DOMAIN_FILTER", "DEFI_TASK_FILTER", "ONE_EQUATION", "CASE_RANGE_START", "CASE_RANGE_END"):
        assert inherited_filter + "=" + escaped_quote + escaped_quote in block
    assert "74 case records" in block
    assert "seed provenance verified" in block
    assert "python3 '${EXPERIMENTS_DIR}/portfolio_variance_v3c2.py'" not in block


def test_exp1b_pca_summary_reads_only_the_five_isolated_seed_files():
    repo_root = Path(__file__).resolve().parents[3]
    run_all = (repo_root / "run_all.sh").read_text(encoding="utf-8")
    start = run_all.index('run exp1b_pca "')
    summary_start = run_all.index("PYEOF_SUMMARY_1B", start)
    summary_end = run_all.index("PYEOF_SUMMARY_1B", summary_start + len("PYEOF_SUMMARY_1B"))
    summary_block = run_all[summary_start:summary_end]

    assert "PCA15_DIR / f'hypatiax_defi_benchmark_pca_results_seed{s}.json'" in summary_block
    assert "(42, 99, 123, 777, 2024)" in summary_block
    assert "PCA15_DIR.glob('*.json')" not in summary_block
    assert "seed provenance mismatch" in summary_block
    assert "must contain 74 case records" in summary_block
