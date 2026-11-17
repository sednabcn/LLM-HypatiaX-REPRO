# Exp2 smoke run 44087232173: undefined error-ratio diagnosis

## Scope and evidence

This report diagnoses the 3-equation × 6-method smoke run:

- Run: [44087232173](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/44087232173)
- Artifact: [exp2-feynman-extrap-smoke-44087232173-attempt-1](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/44087232173/artifacts/14329224197)
- Artifact file: `benchmark_results_extrap.json`
- Scorer: `hypatiax/experiments/benchmarks/exp2_extrapolation_core.py`
- Scope: three Feynman mechanics equations, six methods, 18 method/equation rows.

This is a diagnosis of that smoke run, not a claim about all equations, seeds, or future runs.

## Finding

All 11 null `extrap_error_pct` values are mathematically undefined denominator cases, not missing far predictions or predictor-route failures.

For every one of the 11 rows:

- `extrap_rmse_far` is finite and exactly `0.0`;
- `extrap_diagnostic.status` is `scored`;
- `extrap_diagnostic.error_pct_status` is `zero_or_invalid_training_rmse`;
- `extrap_diagnostic.error_pct_route_consistent` is `true`.

The shared scorer first validates the training targets and training predictions for shape and finiteness. It then calls `calculate_extrapolation_error`, which returns `None` when the computed training RMSE is non-finite or less than or equal to zero. The persisted status combines these cases as `zero_or_invalid_training_rmse`; it does not distinguish exact zero from a non-finite RMSE caused during metric calculation. The exact numeric denominator is not persisted, so the artifact proves that the ratio is undefined but does not let us independently separate zero from non-finite for every row. Given the exact-fit methods and zero far RMSEs, zero is the likely case, but the raw denominator is needed to prove it row by row.

The exact numeric `RMSE_train` used by the extrapolation ratio is not currently persisted as a separate field in `benchmark_results_extrap.json`. The diagnosis is established by the persisted status, finite-value checks, and scorer implementation; the raw denominator itself should be added to future diagnostics for direct auditability.

## Exact null breakdown

| Equation | Method | Far RMSE | Ratio status | Predictor route |
|---|---|---:|---|---|
| Newton gravity | PureLLM Baseline | 0.0 | zero/invalid training RMSE | symbolic formula fallback |
| Newton gravity | EnhancedHybridSystemDeFi | 0.0 | zero training RMSE | retained final predictor |
| Newton gravity | HybridSystemLLMNN | 0.0 | zero training RMSE | retained final predictor |
| Kinetic energy | PureLLM Baseline | 0.0 | zero training RMSE | symbolic formula fallback |
| Kinetic energy | EnhancedHybridSystemDeFi | 0.0 | zero training RMSE | retained final predictor |
| Kinetic energy | HybridSystemLLMNN | 0.0 | zero training RMSE | retained final predictor |
| Reduced mass | PureLLM Baseline | 0.0 | zero training RMSE | symbolic formula fallback |
| Reduced mass | EnhancedHybridSystemDeFi | 0.0 | zero training RMSE | retained final predictor |
| Reduced mass | HybridSystemLLMNN | 0.0 | zero training RMSE | retained final predictor |
| Reduced mass | SymbolicEngineWithLLM | 0.0 | zero training RMSE | symbolic formula fallback |
| Reduced mass | HybridDiscoverySystem | 0.0 | zero training RMSE | symbolic formula fallback |

The remaining seven rows have positive training RMSE and finite ratios:

| Equation | Method | Far RMSE | `error_pct` |
|---|---|---:|---:|
| Newton gravity | ImprovedNN | 2.759375443786179e-12 | 541.1807% |
| Newton gravity | SymbolicEngineWithLLM | 1.3497309822783845e-18 | 97.2818% |
| Newton gravity | HybridDiscoverySystem | 3.4517478110496847e-11 | 97.2807% |
| Kinetic energy | ImprovedNN | 152.96010537204072 | 437.8518% |
| Kinetic energy | SymbolicEngineWithLLM | 0.002018500184759982 | 158.4973% |
| Kinetic energy | HybridDiscoverySystem | 4202.642399477915 | 158.5368% |
| Reduced mass | ImprovedNN | 0.05021972580137786 | 1409.7637% |

## Important interpretation

1. **Null does not mean failed.** All 11 rows have valid far R² and far RMSE, and their far RMSE is exactly zero.
2. **Do not replace null with 0%.** A zero numerator divided by a zero denominator is undefined; a non-finite denominator is also invalid. Reporting 0% would incorrectly imply a positive training baseline and perfect relative stability.
3. **The separate benchmark `rmse` field is not the ratio denominator.** It is the ordinary benchmark result RMSE, whereas the ratio denominator is recomputed by the extrapolation scorer on the exact 80% extrapolation-training partition. For example, EnhancedHybridSystemDeFi has a nonzero ordinary benchmark RMSE on Newton gravity and kinetic energy, while its extrapolation training baseline is zero.
4. **Predictor consistency is not the cause.** All 18 rows record consistent train/far routes. The 11 null rows are not route mismatches or missing retained predictors.
5. **The metric is uninformative for exact-fit rows.** When the training RMSE is zero or invalid, report the absolute metrics and a precise denominator status. Do not rank these methods by the ratio.

## Reporting and instrumentation improvements

For future smoke artifacts, persist these fields per method/equation:

- `extrap_rmse_train`: the exact training-partition RMSE used as the denominator;
- `extrap_rmse_far`: the far-partition RMSE;
- `extrap_error_pct`;
- `error_pct_status`;
- `predictor_route`, `training_prediction_route`, and route-consistency flag.

Prefer distinct statuses such as `zero_training_rmse` and `nonfinite_training_rmse`. Keep predictor-evaluation status separate from ratio-definedness. The current `zero_or_invalid_training_rmse` status is not sufficiently granular to identify the exact arithmetic cause. Persist the numeric denominator and a precise reason.

## Overall result context

The smoke validator passed with 18/18 far R² values, 18/18 far RMSE values, and 7/18 mathematically defined ratios. All six methods executed. The 11 null ratios should be counted as undefined metric outcomes, not missing predictions or method failures. The current artifact does not expose the raw denominator needed to distinguish zero from non-finite training RMSE for every row.

This three-equation smoke is a narrow engineering/diagnostic check. It does not establish broad scientific generalization or comparative superiority.
