# LLM-HypatiaX-REPRO

![Reproducibility](https://img.shields.io/badge/Reproducibility-4A90D9?style=flat-square)
![Symbolic Regression](https://img.shields.io/badge/Symbolic%20Regression-7B2D8B?style=flat-square)
![Hybrid LLM](https://img.shields.io/badge/Hybrid%20LLM-E8A020?style=flat-square)
![Neural Network](https://img.shields.io/badge/Neural%20Network-27AE60?style=flat-square)
![Benchmarks](https://img.shields.io/badge/Benchmarks-E74C3C?style=flat-square)
![Experiments](https://img.shields.io/badge/Experiments-16A085?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-2C3E50?style=flat-square)
![Validation](https://img.shields.io/badge/Validation-8E44AD?style=flat-square)
![Result Verification](https://img.shields.io/badge/Result%20Verification-C0392B?style=flat-square)
![Scientific Research](https://img.shields.io/badge/Scientific%20Research-1A5276?style=flat-square)

## Structure

```
├── .github/
│   ├── scripts/
│   │   ├── locate_analysis_input.sh
│   │   ├── merge_extrap_into_benchmark.py
│   │   ├── merge_shards.py
│   │   ├── run_analysis.py
│   │   └── validate_analysis_input.py
│   └── workflows/
│       ├── ci_analysis.yml
│       ├── ci_paper_audit.yml
│       ├── ci_paper_notebooks.yml
│       ├── ci_pipeline.yml
│       ├── ci_pipeline_analysis.yml
│       ├── ci_pipeline_check.yml
│       ├── ci_postprocess.yml
│       ├── ci_purge_runs.yml
│       ├── ci_report.yml
│       ├── ci_runner.yml
│       ├── ci_runner_disclosure.yml
│       ├── ci_trace_pipeline.yml
│       ├── clean-old-workflows.yml
│       ├── cleanup-cache-actions.yml
│       ├── cleanup-prs.yml
│       └── static.yml
├── config/
│   └── repro.yaml
├── docs/
│   └── architecture.md
├── hypatiax/
│   ├── analysis/
│   │   └── analyze_hybrid_performance.py
│   ├── core/
│   │   ├── base_pure_llm/
│   │   │   └── baseline_pure_llm_defi_discovery.py
│   │   ├── generation/
│   │   │   ├── hybrid_all_domains/
│   │   │   │   └── suite_hybrid_system_all_domains.py
│   │   │   ├── hybrid_all_domains_llm_nn/
│   │   │   │   └── hybrid_system_llm_nn_all_domains.py
│   │   │   ├── hybrid_defi_llm_guided/
│   │   │   │   └── llm_guided_symbolic_discovery_defi.py
│   │   │   └── hybrid_defi_system/
│   │   │       ├── complete_defi_hybrid_system.py
│   │   │       └── hybrid_system_nn_defi_domain.py
│   │   └── training/
│   │       ├── adaptive_config.py
│   │       ├── baseline_neural_network.py
│   │       └── baseline_neural_network_defi_improved.py
│   ├── experiments/
│   │   ├── benchmarks/
│   │   │   ├── exp3_nguyen12_hybrid50v_02.py
│   │   │   ├── hypatia.py
│   │   │   ├── hypatiax_defi_benchmark_v3c.py
│   │   │   ├── run_comparative_suite_benchmark_pca.py
│   │   │   ├── run_comparative_suite_benchmark_v2.py
│   │   │   ├── run_dual_condition_benchmark.py
│   │   │   ├── run_dual_sweep_benchmarks.py
│   │   │   ├── run_hybrid_system_benchmark.py
│   │   │   ├── run_instability_suite.py
│   │   │   ├── run_noise_sweep_benchmark.py
│   │   │   └── run_sample_complexity_benchmark.py
│   │   └── tests/
│   │       └── test_enhanced_defi_extrapolation.py
│   ├── protocols/
│   │   ├── experiment_protocol_all_30.py
│   │   ├── experiment_protocol_benchmark_v2.py
│   │   ├── experiment_protocol_defi.py
│   │   └── experiment_protocol_nguyen12.py
│   ├── reproducibility/
│   │   └── hash_lock.py
│   └── tools/
│       ├── symbolic/
│       │   ├── hybrid_system_v50_2.py
│       │   ├── physics_aware_regressor.py
│       │   └── symbolic_engine.py
│       ├── utils/
│       │   └── __init__.py
│       ├── validation/
│       │   ├── dimensional_validator.py
│       │   ├── domain_validator.py
│       │   ├── ensemble_validator.py
│       │   └── symbolic_validator.py
│       └── visualizations/
│           └── plot_results.py
├── scripts/
│   ├── patches/
│   │   ├── apply_patches.py
│   │   ├── generate_exp2_pca_comparison_table.py
│   │   ├── generate_nguyen12_symequiv_table.py
│   │   ├── generate_patches.py
│   │   ├── issue_registry.json
│   │   ├── paper_targets.json
│   │   ├── run_audit.sh
│   │   ├── trace_pipeline.py
│   │   └── verify_results.py
│   ├── generate_figures.py
│   └── generate_tables.py
├── tests/
│   ├── __init__.py
│   └── test_smoke.py
├── utils/
├── .gitignore
├── Makefile
├── requirements.txt
├── run_all.sh
└── run_all_checkpoint.py
```

## Workflows (16)

- `.github/workflows/ci_analysis.yml` — 8 transitive dependencies
- `.github/workflows/ci_paper_audit.yml` — 4 transitive dependencies
- `.github/workflows/ci_paper_notebooks.yml` — 2 transitive dependencies
- `.github/workflows/ci_pipeline.yml` — 0 transitive dependencies
- `.github/workflows/ci_pipeline_analysis.yml` — 10 transitive dependencies
- `.github/workflows/ci_pipeline_check.yml` — 1 transitive dependencies
- `.github/workflows/ci_postprocess.yml` — 5 transitive dependencies
- `.github/workflows/ci_purge_runs.yml` — 0 transitive dependencies
- `.github/workflows/ci_report.yml` — 1 transitive dependencies
- `.github/workflows/ci_runner.yml` — 33 transitive dependencies
- `.github/workflows/ci_runner_disclosure.yml` — 23 transitive dependencies
- `.github/workflows/ci_trace_pipeline.yml` — 39 transitive dependencies
- `.github/workflows/clean-old-workflows.yml` — 0 transitive dependencies
- `.github/workflows/cleanup-cache-actions.yml` — 0 transitive dependencies
- `.github/workflows/cleanup-prs.yml` — 0 transitive dependencies
- `.github/workflows/static.yml` — 0 transitive dependencies

## File inventory (57 files)

| File | Type |
|------|------|
| `.github/scripts/locate_analysis_input.sh` | shell |
| `.github/scripts/merge_extrap_into_benchmark.py` | python |
| `.github/scripts/merge_shards.py` | python |
| `.github/scripts/run_analysis.py` | python |
| `.github/scripts/validate_analysis_input.py` | python |
| `.github/workflows/ci_trace_pipeline.yml` | config |
| `config/repro.yaml` | config |
| `hypatiax/analysis/analyze_hybrid_performance.py` | python |
| `hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py` | python |
| `hypatiax/core/generation/hybrid_all_domains/suite_hybrid_system_all_domains.py` | python |
| `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py` | python |
| `hypatiax/core/generation/hybrid_defi_llm_guided/llm_guided_symbolic_discovery_defi.py` | python |
| `hypatiax/core/generation/hybrid_defi_system/complete_defi_hybrid_system.py` | python |
| `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py` | python |
| `hypatiax/core/training/adaptive_config.py` | python |
| `hypatiax/core/training/baseline_neural_network.py` | python |
| `hypatiax/core/training/baseline_neural_network_defi_improved.py` | python |
| `hypatiax/experiments/benchmarks/exp3_nguyen12_hybrid50v_02.py` | python |
| `hypatiax/experiments/benchmarks/hypatia.py` | python |
| `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py` | python |
| `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py` | python |
| `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py` | python |
| `hypatiax/experiments/benchmarks/run_dual_condition_benchmark.py` | python |
| `hypatiax/experiments/benchmarks/run_dual_sweep_benchmarks.py` | python |
| `hypatiax/experiments/benchmarks/run_hybrid_system_benchmark.py` | python |
| `hypatiax/experiments/benchmarks/run_instability_suite.py` | python |
| `hypatiax/experiments/benchmarks/run_noise_sweep_benchmark.py` | python |
| `hypatiax/experiments/benchmarks/run_sample_complexity_benchmark.py` | python |
| `hypatiax/experiments/tests/test_enhanced_defi_extrapolation.py` | python |
| `hypatiax/protocols/experiment_protocol_all_30.py` | python |
| `hypatiax/protocols/experiment_protocol_benchmark_v2.py` | python |
| `hypatiax/protocols/experiment_protocol_defi.py` | python |
| `hypatiax/protocols/experiment_protocol_nguyen12.py` | python |
| `hypatiax/reproducibility/hash_lock.py` | python |
| `hypatiax/tools/symbolic/hybrid_system_v50_2.py` | python |
| `hypatiax/tools/symbolic/physics_aware_regressor.py` | python |
| `hypatiax/tools/symbolic/symbolic_engine.py` | python |
| `hypatiax/tools/utils/__init__.py` | python |
| `hypatiax/tools/validation/dimensional_validator.py` | python |
| `hypatiax/tools/validation/domain_validator.py` | python |
| `hypatiax/tools/validation/ensemble_validator.py` | python |
| `hypatiax/tools/validation/symbolic_validator.py` | python |
| `hypatiax/tools/visualizations/plot_results.py` | python |
| `requirements.txt` | other |
| `run_all.sh` | shell |
| `run_all_checkpoint.py` | python |
| `scripts/generate_figures.py` | python |
| `scripts/generate_tables.py` | python |
| `scripts/patches/apply_patches.py` | python |
| `scripts/patches/generate_exp2_pca_comparison_table.py` | python |
| `scripts/patches/generate_nguyen12_symequiv_table.py` | python |
| `scripts/patches/generate_patches.py` | python |
| `scripts/patches/issue_registry.json` | config |
| `scripts/patches/paper_targets.json` | config |
| `scripts/patches/run_audit.sh` | shell |
| `scripts/patches/trace_pipeline.py` | python |
| `scripts/patches/verify_results.py` | python |

## License

This reproducibility repository is licensed under the **Apache License 2.0**.

```
Copyright 2026 PhD Ruperto P. Bonet Chaple

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

Original **HypatiaX** work © PhD Ruperto P. Bonet Chaple.  
See [`LICENSE`](./LICENSE) for the full license text.

---
*Generated by scan_workflows.py*
