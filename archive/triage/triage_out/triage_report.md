# Step 1: Freeze & triage report

Generated: 2026-10-23T14:08:31+00:00  |  root: `/home/agagora/Downloads/GITHUB/LLM-HypatiaX-REPRO`

## 1. Snapshot
- Git SHA: `9923dd5b774e2bd33b767ea6b7f7a785af2ee6cc`  branch: `audit/option3`
- Working tree dirty: **True** (35 changed files)
- Code/config files checksummed: 134

## 2. Stray files

- none

## 3. Results triage

| status | files |
|---|---|
| candidate_clean | 0 |
| exploratory | 260 |
| superseded | 172 |
| corrupt | 0 |

Default is `exploratory`; `candidate_clean` requires provenance showing a live run with both flags = 1. Per-file reasons are in `results_status.csv`.

## 4. Conflict markers

- `hypatiax/tools/__init__.py` lines [2, 4, 6]: markers present but file parses: probably inside a string/docstring; verify

## 5. Patches

- `all_domains_and_recovery_tests.patch`: ALREADY APPLIED (reverse applies cleanly)
- `followup_fixes.patch`: does not apply: 1 out of 1 hunk FAILED
- `hybrid-ingest-test.patch`: not testable (target files absent or `patch` unavailable)
    - suspicious target prefix: rsc/experiments/tests/test_stats_ingest.py (typo for hypatiax/ ?)
    - target file missing in this tree: rsc/experiments/tests/test_stats_ingest.py
- `repro-adaptive-config.patch`: does not apply: 1 out of 2 hunks FAILED
- `repro-metrics-api.patch`: ALREADY APPLIED (reverse applies cleanly)
- `rule_a_fixes.patch`: does not apply: 9 out of 9 hunks FAILED

## 6. Remaining scan errors (scan_after3.txt)

- **[clean-run]** .github/workflows/ci_bypass_audit.yml  HYPATIAX_DISABLE_HARDCODED present but not set to 1
    - action: set HYPATIAX_DISABLE_HARDCODED=1 or document that outputs never feed headline tables
- **[config-path]** config/repro.yaml  benchmarks.core15.script not found: hypatiax/experiments/benchmarks/run_dual_condition_benchmark.py
    - action: fix the script path in config/repro.yaml or restore the script
- **[config-path]** config/repro.yaml  benchmarks.instability.script not found: hypatiax/experiments/benchmarks/run_dual_sweep_benchmarks.py
    - action: fix the script path in config/repro.yaml or restore the script
- **[evaluator]** hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:3748  absolute ss_tot guard (Supplement A Fix 5 / Listing 8 defect)
    - action: replace absolute ss_tot guard with core.r2_canonical.r2_checked (Rule A)
- **[import]** hypatiax/tools/symbolic/hybrid_system_v50_2.py:615  unresolved import: hypatiax.tools.llm_providers.anthropic_provider
    - action: create/restore the missing module or remove the dead import
- **[import]** hypatiax/tools/symbolic/hybrid_system_v50_2.py:627  unresolved import: hypatiax.tools.llm_providers.google_provider
    - action: create/restore the missing module or remove the dead import
- **[merge-conflict]** hypatiax/tools/__init__.py:2  conflict marker
    - action: open the file; if markers are real resolve them, if inside a string ignore
- **[merge-conflict]** hypatiax/tools/__init__.py:4  conflict marker
    - action: open the file; if markers are real resolve them, if inside a string ignore
- **[merge-conflict]** hypatiax/tools/__init__.py:6  conflict marker
    - action: open the file; if markers are real resolve them, if inside a string ignore
- **[parse]** hypatiax/data/results/ablation/exp1_ablation/exp1_ablation_run.log__shard0_rescued_1786497899.json:1  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    - action: recover the original JSON from the shard/log or mark file corrupt (do not cite)
- **[parse]** hypatiax/data/results/ablation/exp1_ablation/exp1_ablation_run.log__shard1_rescued_1786493709.json:1  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    - action: recover the original JSON from the shard/log or mark file corrupt (do not cite)
- **[parse]** hypatiax/data/results/ablation/exp1_ablation/exp1_ablation_run.log__shard2_rescued_1786493416.json:1  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    - action: recover the original JSON from the shard/log or mark file corrupt (do not cite)
- **[parse]** hypatiax/data/results/ablation/exp1_ablation/instability_extrapolation_v2.csv__shard0_rescued_1786497899.json:1  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    - action: recover the original JSON from the shard/log or mark file corrupt (do not cite)
- **[parse]** hypatiax/data/results/ablation/exp1_ablation/instability_extrapolation_v2.csv__shard1_rescued_1786493709.json:1  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    - action: recover the original JSON from the shard/log or mark file corrupt (do not cite)
- **[parse]** hypatiax/data/results/ablation/exp1_ablation/instability_extrapolation_v2.csv__shard2_rescued_1786493416.json:1  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    - action: recover the original JSON from the shard/log or mark file corrupt (do not cite)
- **[undefined-name]** hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:3478  undefined name '_kill_thread'
    - action: add the missing import/definition (e.g. `import subprocess`, define _kill_thread)
- **[undefined-name]** hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:3025  undefined name 'subprocess'
    - action: add the missing import/definition (e.g. `import subprocess`, define _kill_thread)

## 7. Blocking issues

- git working tree is dirty (35 files): commit or stash before any confirmatory run
- followup_fixes.patch does not apply cleanly
- hybrid-ingest-test.patch has a suspicious target path
- repro-adaptive-config.patch does not apply cleanly
- rule_a_fixes.patch does not apply cleanly
- 17 unresolved scan error(s) in scan_after3.txt
