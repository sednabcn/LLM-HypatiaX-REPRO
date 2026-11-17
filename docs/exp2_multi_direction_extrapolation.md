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
