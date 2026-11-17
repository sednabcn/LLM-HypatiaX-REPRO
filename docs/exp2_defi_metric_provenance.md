# Exp2 DeFi metric and predictor provenance

## Why this audit exists

The DeFi adapter calls `hybrid_predict(description, domain, X, y, ...)` with
the complete runner input arrays. Its selected evaluation dictionary supplies
the method-level `r2` and `rmse`; those metrics therefore describe the full
input dataset unless the backend explicitly reports another scope.

The shared extrapolation scorer separately calls the retained final predictor
on the exact contiguous extrapolation training partition and the far
partition. Those are different row populations. A numeric difference between
the wrapper's full-input RMSE and `extrap_rmse_train` is not evidence by itself
that the retained predictor disagrees with the backend. They must not be
compared as if they used identical rows.

## Recorded provenance

The DeFi method result now records:

- `evaluation_source_key`: which returned result branch supplied the selected
  evaluation dictionary (for example `evaluation`, `nn_result`, or
  `result`).
- `evaluation_metric_source`: the exact `rmse`, `sqrt_mse`, or
  prediction-recomputed route that supplied the reported metric.
- `benchmark_metric_row_scope` and `benchmark_metric_row_count`: the full
  input dataset scope and row count passed to the adapter.
- `evaluation_prediction_source` and row count: selected nested/top-level
  prediction array, formula replay, or synthetic R²/RMSE reconstruction.
- `evaluation_feature_representation`: runner input feature names, count,
  and row count.
- `formula_replay_status` and maximum absolute difference: whether the
  candidate symbolic formula reproduces the selected prediction array.
- `residual_correction_attempted` / `residual_correction_applied`.
- `final_predictor_composition`: formula base plus residual NN, formula base,
  or unavailable.

These fields are copied into the extrapolation diagnostic and its JSON
artifact so the audit is visible alongside the metrics.

## Scope-aware RMSE comparison

The shared scorer always preserves the raw `benchmark_rmse` and exact
`extrap_rmse_train`. It computes a delta and a boolean consistency result only
when the benchmark RMSE row scope is `extrapolation_train` or is unspecified
for legacy adapters. When an adapter declares a different scope, it sets
`train_rmse_consistency_status = not_comparable_different_row_scope` and
leaves the delta and boolean comparison null.

The ratio `error_pct = 100 * RMSE_far / RMSE_train` continues to use the
retained final predictor on the exact extrapolation train and far partitions.
This change does not replace metrics, change the ratio definition, fit a model,
or launch an experiment.

## Limits

The recorded row scope is the adapter's known call contract: full `X`/`y`
input. It does not independently prove which internal backend array produced
every nested metric. The source key and selected prediction provenance make
that branch inspectable, while a deeper backend audit would be needed if the
backend internally subsets or transforms rows before computing its metric.
