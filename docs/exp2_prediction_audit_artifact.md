# Exp2 row-level prediction audit artifact

## Purpose

The multi-direction extrapolation protocol emits a distinct result for each
equation and feature-wise or joint direction. Aggregate far-region R²/RMSE
alone are not sufficient to independently inspect those results. This change
persists the aligned target and prediction vectors used by the scorer.

## Artifact shape

Each protocol test record contains an `extrap_prediction_audit` mapping keyed
by method name. Each method entry is one of:

- `recomputed_from_aligned_far_predictions`: includes `y_true`, `y_pred`,
  `row_count`, `prediction_source`, and the matching recomputed `r2` and
  `rmse`.
- `predictions_unavailable`: includes null prediction arrays, zero row
  count, and null prediction source. This is an explicit outcome, not a
  fabricated or reconstructed vector.

The same method-level audit object is copied into the flat
`benchmark_results_extrap*.json` row. The protocol-level and flat artifacts
therefore retain the same equation, direction, method, and prediction
provenance.

Prediction sources distinguish the retained final fitted predictor from the
symbolic-formula fallback. For hybrid methods, the retained final predictor
remains authoritative when available; the audit never substitutes a base
formula for a fitted composite predictor.

## Validation

The Exp2 smoke validator now fails closed when the audit mapping or method
coverage is missing. For each available prediction vector it checks:

1. Target and prediction arrays are numeric, finite, and exactly aligned to
   the recorded far-region row count.
2. RMSE recomputed from the saved arrays matches both the audit RMSE and the
   published far RMSE.
3. Canonical R² recomputed from the saved arrays matches both the audit R² and
   the published far R², including null handling for undefined/catastrophic
   scores.
4. The flat artifact preserves the exact per-method audit object from the
   protocol record.

Unavailable predictions must not contain partial arrays. They remain counted
as unavailable in the smoke summary rather than being silently treated as
verified.

## Scope and limitations

This records the exact row-level far predictions produced by the existing
scoring route. It does not save training prediction arrays, feature matrices,
or model weights, and it does not make an unavailable neural predictor
replayable. The audit supports independent metric recomputation, not
independent reproduction of model fitting.

The change updates the shared scorer, both active Feynman runners, flat
artifact export, smoke validation, offline regression fixtures, and this
documentation. It does not launch experiments, workers, benchmarks, model
fitting, or LLM/API calls. No local tests were run while preparing this PR;
CI is the verification mechanism.


## Near-zero training-error fallback score

The legacy ratio `error_pct = 100 * RMSE_far / RMSE_train` is suppressed
when training RMSE is below the scale-aware threshold
`epsilon_train = 1e-12 * max(1, std(y_train))`.

In that case the scorer publishes the fallback
`extrap_nrmse_far = RMSE_far / std(y_train)`. This is a dimensionless,
lower-is-better score normalized by the variation of the training targets.
It is also exported as `extrapolation_score`, with
`extrap_nrmse_far_status` describing availability. If the training-target
standard deviation is zero or non-finite, the fallback remains null with an
explicit status; raw far RMSE and far R² remain independently available.
Diagnostics record the epsilon and target scale. Both active Feynman runners
export the score in their flat result rows. This is a scoring-only code change;
no experiments or benchmarks are launched.
