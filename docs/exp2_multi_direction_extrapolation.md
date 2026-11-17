# Exp2 multi-direction extrapolation protocol

## Purpose

The previous Exp2 extrapolation split sorted every equation by its first input
column. That measured only one coordinate direction and could hide failures
along other independent variables. This protocol now creates a separate
train/far split for every input feature, plus one joint high-input direction.

Each direction is a distinct test record. All six methods are trained afresh
on that direction's training partition; no fitted model is reused across
directions.

## Direction definitions

- **Feature-wise direction:** sort rows by one original input column, retain
  the complete feature matrix, train on the lower `train_frac` portion, and
  score the remaining rows within the configured multiplier boundary.
- **Joint direction:** convert each input column to empirical percentile
  ranks, average those ranks per row, and split on that joint score. This
  emphasizes rows that are jointly high across the input dimensions without
  fitting a scaler or using target values to define the split.

For a two-variable kinetic-energy equation, the runner therefore emits
mass-only, velocity-only, and joint-direction records. Equations with more
inputs receive one independent direction per input plus the joint direction.

Direction identity is included in the test description
(`[extrap:<feature-name>]` or `[extrap:joint]`) and split metadata
(`extrap_direction`, `extrap_feature_index`, and
`extrap_direction_score`). Flat benchmark rows inherit the direction-specific
test description, so results remain separately addressable.

## Data separation and leakage controls

- The split uses only the input matrix and row order; target values are carried
  along solely to preserve alignment and compute the final far-region metrics.
- No far-region rows are passed to method fitting. Every direction receives a
  newly constructed training partition.
- The joint direction uses empirical ranks of inputs only. It does not inspect
  targets, model predictions, formulas, or far-region scores.
- A split that cannot provide at least two training and two far rows fails
  closed; there is no in-sample fallback.
- The existing multiplier clipping rule applies to the selected direction
  score. For joint direction this score is in percentile-rank units.

## Interpretation limits

The joint mean-percentile direction is a reproducible stress direction, not a
full factorial design. It does not guarantee that every far row exceeds the
training maximum in every feature, particularly when input variables are
correlated. Feature-wise splits isolate one coordinate's ordering but retain
the naturally sampled values of the other features; they do not constitute
controlled interventions on a physical system.

For stronger causal isolation, the data generator should later support
controlled one-variable and joint-range sampling. That is a separate protocol
extension and must preserve the equation's physical constraints.

The number of test records is now the sum, over equations, of
(number of input features + one joint direction). Validators therefore check
the six-method coverage for every direction-specific record rather than
assuming exactly 18 equation/method rows.

## Execution boundary

This change updates split construction, runner orchestration, offline
regression tests, and output validation only. It does not launch experiments,
workers, benchmarks, model fitting, or LLM/API calls. The new protocol must be
run explicitly by the repository owner to produce new performance evidence.

## Smoke results: run #44139260074

Run [#44139260074](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/44139260074)
completed successfully on 2026-11-17. Its artifact and validator establish the
following for the three equation-direction records that actually ran:

- 18/18 method rows have far-region R² and RMSE.
- 18/18 row-level far-prediction audits were verified against their saved
  aligned `y_true`/`y_pred` arrays (24 far rows per method); recomputed R²
  and RMSE matched the published far metrics.
- `error_pct` is available for 9/18 rows. The other 9 are null because their
  training RMSE denominator is exactly zero, making
  `100 * RMSE_far / RMSE_train` undefined. This is not a missing far RMSE.
- The null `error_pct` rows are PureLLM, EnhancedHybridSystemDeFi, and
  HybridSystemLLMNN for each of the three equations. In the run log the two
  hybrid methods report in-domain RMSE as `0.000000`; their far RMSE remains
  present and their far R² is 1.0000 in these records. The shared scorer uses
  the retained final predictor to calculate the training baseline and
  deliberately leaves the ratio null when that baseline is zero. This is a
  denominator/metric-definition outcome, not evidence that the hybrid
  predictors failed to produce predictions.
- ImprovedNN, SymbolicEngineWithLLM, and HybridDiscoverySystem have nonzero
  training RMSE in these records, so their error percentages can be computed.

### Far-region R² observed in this run

| Equation / direction actually executed | PureLLM | ImprovedNN | DeFi hybrid | LLMNN hybrid | Symbolic engine | Hybrid discovery |
|---|---:|---:|---:|---:|---:|---:|
| Newton gravity [m1] | 1.0000 | 0.9989 | 1.0000 | 1.0000 | 1.0000 | 0.6467 |
| Kinetic energy [m] | 1.0000 | 0.9982 | 1.0000 | 1.0000 | 1.0000 | -0.8956 |
| Reduced mass [m1] | 1.0000 | 0.9989 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

These are results from one noiseless smoke run, not repeated-seed estimates.
R² is shown here; the artifact contains the row-level predictions and RMSE
values for exact audit. Near-perfect results for the LLM/hybrid methods should
also be interpreted in light of the zero training residuals and the fact that
the DeFi hybrid and PureLLM paths can share formula-generation provenance.

### Direction-coverage limitation

Despite the feature-wise/joint protocol implemented earlier, this workflow
execution produced only three direction-specific records:

- Newton gravity: `m1`
- Kinetic energy: `m`
- Reduced mass: `m1`

It did not execute the other feature directions or any joint direction. For
the three equations' input widths (3, 2, and 2), the intended protocol would
produce 4 + 3 + 3 = 10 equation-direction records, or 60 method rows. This
run produced 3 records and 18 method rows. Therefore it validates the
prediction-audit path and the observed `m1`/`m` directions only; it is not
evidence for full multi-direction coverage. The successful workflow status
must not be read as proof that all ten directions ran.

The workflow log also reports that exporting the separate
`benchmark_results.json` file failed because `_FLAT_OUTPUT_DIR` was not
defined. The extrapolation flat file, protocol JSON, prediction audits, and
smoke validator did complete successfully; the export warning should be
tracked separately.

### Metric interpretation: zero training RMSE

The shared scorer computes the ratio only when both RMSE values are finite
and the training RMSE is strictly positive. For a retained final predictor,
it predicts the exact extrapolation training partition using that same
predictor. If this produces `RMSE_train = 0`, then the ratio has a zero
denominator and `error_pct` is intentionally null with status
`zero_training_rmse`. Far-region RMSE is calculated independently and is
not nulled by this condition.

This distinction should be retained in reports:

- `extrap_rmse_far = null`: far prediction or far metric is unavailable or
  invalid; inspect the far diagnostic status.
- `error_pct = null` with `zero_training_rmse`: far RMSE may be fully
  available, but the relative-to-training ratio is mathematically undefined.

The run artifact is available at
[workflow artifact 14353183964](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/44139260074/artifacts/14353183964).

