# Exp2 smoke run 44103361650: zero RMSE and null error-ratio diagnosis

## Executive summary

Run [44103361650](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/44103361650)
completed successfully on `master`, commit
`6916f826adfcac002fae4d1e13fde49c4310ffe3` (the PR #164 merge).

The artifact contains 18 method/equation rows. Far-region R² and RMSE are
available for all 18. Ten rows have a null `extrap_error_pct`; these are not
null RMSE values:

- `extrap_r2_far = 1.0`
- `extrap_rmse_far = 0.0`
- `extrap_rmse_train = 0.0`
- `extrap_error_pct = null`

The ratio is defined as `100 * extrap_rmse_far / extrap_rmse_train`.
When both RMSE values are zero, this is `0 / 0`, which is undefined. It must
not be replaced with 100, 1.0, an epsilon denominator, or another fabricated
number. Here, **R² = 1.000** is the perfect-fit score; **RMSE = 0.000** is the
zero-error score. They are different metrics.

## Exact null rows

| Method | Equation | Far R² | Far RMSE | Train RMSE | Benchmark RMSE | Consistency |
|---|---|---:|---:|---:|---:|---|
| PureLLM | Newton gravity | 1.000 | 0 | 0 | 0 | matches |
| EnhancedHybridSystemDeFi | Newton gravity | 1.000 | 0 | 0 | 1.042593444e-13 | mismatch |
| HybridSystemLLMNN | Newton gravity | 1.000 | 0 | 0 | 0 | matches |
| PureLLM | Kinetic energy | 1.000 | 0 | 0 | 0 | matches |
| EnhancedHybridSystemDeFi | Kinetic energy | 1.000 | 0 | 0 | 5.4989468501 | mismatch |
| HybridSystemLLMNN | Kinetic energy | 1.000 | 0 | 0 | 0 | matches |
| PureLLM | Reduced mass | 1.000 | 0 | 0 | 0 | matches |
| EnhancedHybridSystemDeFi | Reduced mass | 1.000 | 0 | 0 | 0.004056770934 | mismatch |
| HybridSystemLLMNN | Reduced mass | 1.000 | 0 | 0 | 0 | matches |
| HybridDiscoverySystem | Reduced mass | 1.000 | 0 | 0 | 0 | matches |

The other eight rows have non-null ratios. This is 18/18 far R² and RMSE
coverage, and 8/18 defined ratio coverage.

## Why the methods return these values

### Exact formula / predictor routes

The artifact records these formulas or predictor routes:

- PureLLM returns the expected closed-form Newton gravity, kinetic energy,
  and reduced-mass equations. The symbolic formula fallback evaluates exactly
  against the generated targets in this smoke data.
- HybridSystemLLMNN retains its final predictor and that predictor evaluates
  exactly on the training and far partitions for these three equations.
- HybridDiscoverySystem's reduced-mass formula
  `(m2 * m1) / (m1 + m2)` is algebraically equivalent to the target and
  evaluates exactly on both partitions.

For these rows, zero RMSE and R² = 1.0 are consistent with exact predictions.
The null ratio is solely the mathematically undefined zero denominator, not
a failed RMSE calculation or unavailable far prediction.

### EnhancedHybridSystemDeFi: a separate metric-provenance discrepancy

All three DeFi rows have exact zero RMSE when the retained final predictor is
replayed on the exact extrapolation train and far partitions. However, the
method result's ordinary benchmark RMSE is nonzero for all three rows.

The v2 adapter's inspected control flow explains where this discrepancy can
arise:

1. It initially extracts `r2` and `rmse` from the backend `eval_` result.
2. It separately obtains backend `y_pred` (or evaluates the candidate formula)
   to decide whether a formula predictor can be retained.
3. It can retain that formula as `_predict_fn` when it reproduces the chosen
   base predictions.
4. Unless the residual correction is applied and its replayable composition
   replaces the metric, the original `rmse_val` remains the backend
   evaluation's reported RMSE.

The shared extrapolation scorer correctly uses the retained callable for
both exact training and far rows. The reported benchmark RMSE, however, is
not guaranteed to have been computed from that same callable on those same
rows. The mismatch is therefore a predictor/metric provenance issue, not
evidence that the extrapolation RMSE should be nonzero.

The artifact alone cannot identify the exact backend branch or prove which
internal prediction array produced each nonzero DeFi benchmark RMSE. The
adapter should expose that provenance before any metric is overwritten or
the retained predictor is changed.

## Code change in this PR

The shared scorer previously collapsed a true zero training denominator and
an invalid/non-finite denominator into
`error_pct_status = zero_or_invalid_training_rmse`. It now reports:

- `zero_training_rmse`: finite training RMSE is exactly zero; ratio is
  mathematically undefined.
- `invalid_training_rmse`: training RMSE is non-finite.
- `invalid_far_rmse`: the far RMSE is invalid when the ratio is attempted.
- `available`: both RMSE values are valid and the training denominator is
  positive.

The numeric metric behavior is unchanged: the far R² and RMSE are preserved,
and `error_pct` remains null for a zero denominator.

An offline regression explicitly asserts the exact-prediction case:
R² = 1.0, far RMSE = 0.0, training RMSE = 0.0, and null ratio with
`zero_training_rmse` status. Existing hybrid regressions now assert the
more precise status.

## Follow-up required for DeFi

Do not change the ratio definition or force a non-null ratio. A separate
method-adapter fix should record, at the point where each metric is computed:

- the source of `eval_` and its decision/branch;
- whether `eval_.y_pred` or top-level `result.y_pred` supplied predictions;
- the prediction route used to compute the reported `r2`/`rmse`;
- whether the retained formula reproduces that exact prediction array;
- whether a residual NN was applied and whether the final callable includes it;
- the row scope and feature representation for each metric.

Then either make the benchmark RMSE represent the same final predictor and
row scope, or report the two metrics under explicitly distinct names. Do not
silently relabel a full-dataset/backend metric as the exact extrapolation
training RMSE.

No benchmark, experiment, worker, model fit, or LLM API call was run while
preparing this diagnosis. The change is limited to scorer status semantics,
offline tests, and documentation.
