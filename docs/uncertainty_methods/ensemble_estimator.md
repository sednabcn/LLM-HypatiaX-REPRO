# Ensemble disagreement estimator

## Scope

EnsembleUncertainty adapts a collection of **already-fitted** regression
predictors to the shared uncertainty-method interface. It never calls a
member's fit(), trains a member, tunes members, or launches an experiment.

Each member must be callable as member(X) or expose member.predict(X).
At least two members are required. All members must return one finite scalar
prediction per input row.

## Example

    from hypatiax.tools.uncertainty_methods import EnsembleUncertainty

    # These predictors must already be fitted by the caller.
    method = EnsembleUncertainty([fitted_model_a, fitted_model_b, fitted_model_c])
    method.fit(X_train, y_train)  # validates shapes/provenance; does not fit members
    estimate = method.estimate(X_test, nominal_coverage=0.90)

    mean_prediction = estimate.mean
    member_disagreement = estimate.scale
    member_draws = estimate.samples

The estimator returns the ensemble mean, sample standard deviation across
members (ddof=1), member predictions as predictive samples, and empirical
member-spread bounds at the requested central quantile levels.

## Interpretation and limitations

- scale measures disagreement among supplied members, not total predictive
  uncertainty. Shared biases and correlated member errors can make disagreement
  deceptively small.
- samples are member predictions, not posterior draws or bootstrap draws.
- lower and upper summarize the empirical spread of member predictions.
  They are **not calibrated prediction intervals** and have no nominal
  coverage guarantee. The requested coverage controls only the empirical
  quantile levels used to summarize the finite member set.
- With small ensembles, empirical quantiles are coarse and may coincide.
- This regression adapter expects one-dimensional targets. Multi-output
  estimators need a separately specified output contract.
- Calibration, if desired, must be performed as a separate stage on a
  disjoint calibration split using an explicit calibration method.

## Lifecycle

1. Fit constituent models outside this adapter, using the appropriate training
   split and dependence-aware protocol.
2. Supply those fitted objects to EnsembleUncertainty.
3. Call adapter fit(X_train, y_train) to validate aligned training data and
   feature count only; it does not refit constituent models.
4. Call estimate(X) on the desired evaluation slice.
5. Evaluate point metrics and interval coverage/width separately, retaining
   the metadata that identifies these bounds as uncalibrated member spread.

The adapter is available through UNCERTAINTY_METHODS.create("ensemble",
members=...) and is exported from hypatiax.tools.uncertainty_methods.
