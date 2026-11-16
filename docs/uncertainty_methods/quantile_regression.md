# Quantile regression

## Core idea

Quantile regression estimates conditional quantiles of the response rather
than only its conditional mean. For probability level tau, it estimates
q_tau(x) such that approximately a fraction tau of outcomes fall below that
conditional quantile.

Quantile regression can represent asymmetric and heteroscedastic conditional
outcome distributions. Lower and upper quantiles can form an interval, but
their empirical coverage must still be evaluated on held-out data.

## Candidate models

- Linear quantile regression: interpretable baseline.
- Gradient-boosted quantile regression: flexible tabular baseline.
- Neural quantile regression: flexible but needs careful regularization.
- Distributional regression: model a full conditional distribution where
  justified, rather than fitting unrelated quantiles.

## Assumptions and failure modes

Quantiles fitted separately can cross (for example, estimated 0.95 below 0.90).
Sparse tails are difficult to estimate. Extrapolated quantiles can behave
implausibly, especially outside feature support. Quantile estimates do not
automatically provide calibrated coverage under shift.

Specify the quantile loss, optimization, regularization, and treatment of
crossing. Rearrangement or monotonic constraints may help but must be evaluated.

## Required outputs and diagnostics

- A mapping from requested probability levels to aligned predictions.
- Pinball loss for each quantile and quantile level.
- Quantile-crossing rate and magnitude.
- Empirical coverage and width for paired lower/upper quantiles.
- Tail sample counts and support diagnostics.

## Evaluation plan

Evaluate pinball loss per quantile, calibration curves, coverage/width, and
crossing before and after any correction. Include heteroscedastic and skewed
synthetic targets. Assess quantile ordering and tail behavior over horizon
distance, not just average in-domain metrics.

## Template

See `hypatiax/tools/uncertainty_methods/templates/quantile_template.py`.
