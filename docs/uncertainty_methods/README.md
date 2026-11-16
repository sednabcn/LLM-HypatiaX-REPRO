# Uncertainty methods: study guide and implementation templates

This directory is a learning and design resource for the next uncertainty-method
implementations. It builds on the shared contracts in
`hypatiax.tools.uncertainty_methods` (introduced on the parent infrastructure
branch).

## Start here

1. Read [shared infrastructure](../uncertainty_methods/shared_infrastructure.md)
   for the common output contract, calibration separation, and result schema.
2. Read [the architecture roadmap](../uncertainty_methods/architecture_and_roadmap.md)
   for data splits and integration boundaries.
3. Study each method guide and its deliberately incomplete Python template.
4. Compare methods using the common evaluation protocol below before selecting
   one for implementation.

## Method guides and templates

| Method | Study guide | Python template | Primary output |
|---|---|---|---|
| Bayesian methods | [bayesian.md](bayesian.md) | [bayesian_template.py](../../hypatiax/tools/uncertainty_methods/templates/bayesian_template.py) | Posterior / posterior-predictive draws |
| Ensembles | [ensembles.md](ensembles.md) | [ensemble_template.py](../../hypatiax/tools/uncertainty_methods/templates/ensemble_template.py) | Member predictions and disagreement |
| Bootstrap | [bootstrap.md](bootstrap.md) | [bootstrap_template.py](../../hypatiax/tools/uncertainty_methods/templates/bootstrap_template.py) | Resampling-based prediction draws |
| Quantile regression | [quantile_regression.md](quantile_regression.md) | [quantile_template.py](../../hypatiax/tools/uncertainty_methods/templates/quantile_template.py) | Conditional quantiles |
| Distribution-shift-aware calibration | [shift_aware_calibration.md](shift_aware_calibration.md) | [shift_aware_template.py](../../hypatiax/tools/uncertainty_methods/templates/shift_aware_template.py) | Calibrated intervals plus support diagnostics |

These are design templates, not usable estimators. They intentionally contain
`NotImplementedError` sections. They must not be registered as available
production methods until completed and tested.

## Common comparison protocol

For each method, preserve the same:
- training/validation/calibration/in-domain-test/extra-domain-test split roles;
- feature preprocessing and target transformation policy;
- evaluation points, horizon directions, distances, and target values;
- nominal interval levels (recommend 0.80, 0.90, 0.95);
- point and interval metrics, plus method-specific diagnostics.

Report at least:
- point accuracy: MAE, RMSE, R² (when defined);
- interval quality: empirical coverage, mean width, interval score;
- calibration gap: empirical minus nominal coverage;
- support/shift diagnostics where applicable;
- runtime, fit failures, prediction failures, and sample counts.

Never compare a Bayesian credible interval, an ensemble standard-deviation band,
and a calibrated prediction interval as if they had identical semantics. Label
each interval. For extrapolation, plot accuracy and coverage against distance;
out-of-domain coverage is empirical evidence for that tested domain, not an
automatic guarantee.

## Recommended implementation sequence

1. Complete the common contract tests and agree the semantics of each estimate field.
2. Implement adapters for supplied ensemble/bootstrap predictions and quantile
   outputs before adding expensive model-fitting backends.
3. Add Bayesian methods with separate latent-function and observation-predictive
   uncertainty.
4. Add shift-aware calibration only after specifying the shift assumptions,
   overlap diagnostics, and calibration split design.
5. Integrate methods with horizon evaluation through a thin adapter; do not
   couple method internals to Feynman equations.

## Research checklist

Before implementing a method, answer:
- What is random: parameters, model members, training samples, outcomes, or calibration scores?
- Does the output describe parameter uncertainty, conditional-mean uncertainty,
  or a future observation?
- Which data are used to fit, tune, and calibrate it?
- What assumptions support any claimed coverage or probability interpretation?
- What happens outside calibration support?
- Which diagnostics can reveal failure or overconfidence?
- What baseline and synthetic negative control will test it?
