# General-purpose prediction intervals and conformal calibration

## Scope

hypatiax.tools.uncertainty adds model-agnostic prediction-interval calibration
and evaluation. It is independent of Feynman equations, estimators, and horizon
generation. It consumes predictions from an already-fitted model and targets
from a separate calibration or evaluation split.

## Split conformal regression

    from hypatiax.tools import SplitConformalRegressor

    # Predictor is already fitted; calibration data were not used for fitting.
    calibrator = SplitConformalRegressor(nominal_coverage=0.95)
    calibrator.fit(y_calibration, predictor.predict(X_calibration))

    lower, upper = calibrator.predict_interval(predictor.predict(X_test))
    metadata = calibrator.calibration_metadata

The method uses absolute calibration residuals and finite-sample rank
k = ceil((n_cal + 1) * coverage). If k exceeds the calibration sample size,
the conservative conformal quantile is positive infinity. This avoids
silently using an anti-conservative quantile when the calibration sample is
too small for the requested nominal level.

The predictor is not fitted, tuned, or changed by the calibrator.

## Evaluate intervals

    from hypatiax.tools import evaluate_prediction_intervals

    metrics = evaluate_prediction_intervals(
        y_true=y_test,
        lower=lower,
        upper=upper,
        nominal_coverage=0.95,
        reference_scale=training_target_std,
    )

Metrics include empirical coverage, mean width, interval score, absolute
coverage gap, sample count, and optional training-scale-normalised width.
evaluate_interval_levels evaluates multiple nominal levels independently.

## Intra-domain versus extra-domain interpretation

Split conformal's usual finite-sample marginal coverage result requires
exchangeability between calibration and evaluation observations. An in-domain
random calibration split may be approximately exchangeable with an in-domain
test split when the sampling design supports that assumption. Extra-domain
evaluation deliberately changes the input distribution, so ordinary split
conformal coverage is NOT guaranteed there.

- Calibrate only on the designated calibration split.
- Never use extra-domain test targets to tune interval radii or choose methods.
- Report intra, boundary, and each extra-domain horizon separately.
- Treat extra-domain empirical coverage as a measured diagnostic, not a
  distribution-free guarantee.
- Report sample counts, nominal level, width, and coverage together.
- Distinguish prediction intervals from confidence intervals for a conditional
  mean, credible intervals, and scenario envelopes.

Absolute-residual split conformal is a baseline, not a universal uncertainty
solution. Heteroscedastic data may require normalised/local conformal scores or
quantile models. Model-form uncertainty may require ensembles, alternative
scientific hypotheses, or sensitivity analysis. None automatically guarantees
coverage under arbitrary extrapolation.

## Scientific safeguards and limitations

1. The calibration set must be disjoint from model fitting and preprocessing
   fitting, unless a documented cross-fitting design is used.
2. The interval evaluator does not estimate uncertainty; it evaluates supplied
   bounds.
3. This implementation provides one transparent split-conformal baseline. It
   does not implement Bayesian inference, bootstrap, ensembles, quantile
   regression, or distribution-shift-robust conformal variants.
4. Infinite intervals are valid conservative outputs when the finite-sample
   conformal rank is unavailable; downstream reporting should preserve them.
5. Coverage is marginal over the evaluation sample and can conceal conditional
   undercoverage. Report it by horizon, direction, method, and task.
6. Do not interpret a nominal 95% interval as a 95% extrapolation guarantee.

## API

- SplitConformalRegressor(nominal_coverage=0.95)
- fit(y_calibration, calibration_predictions)
- quantile(coverage=None)
- predict_interval(predictions, coverage=None)
- calibration_metadata
- evaluate_prediction_intervals(y_true, lower, upper, nominal_coverage, reference_scale=None)
- evaluate_interval_levels(y_true, intervals, reference_scale=None)

No experiment, benchmark, model fitting, or LLM request is performed by these tools.
