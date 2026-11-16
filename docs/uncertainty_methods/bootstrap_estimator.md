# Bootstrap uncertainty estimator

\`BootstrapUncertainty\` provides an explicit, model-factory-based bootstrap
adapter implementing the shared \`UncertaintyMethod\` contract.

## Lifecycle and side effects

Construction and \`estimate()\` do not fit models. Calling \`fit(X_train, y_train)\`
explicitly creates and fits the requested bootstrap replicates. The caller
supplies \`estimator_factory\`, which must return a fresh object exposing
\`fit(X, y)\` and \`predict(X)\`. Reusing a mutable estimator instance is rejected.

\`\`\`python
from sklearn.tree import DecisionTreeRegressor
from hypatiax.tools.uncertainty_methods import BootstrapUncertainty

method = BootstrapUncertainty(
    estimator_factory=lambda: DecisionTreeRegressor(max_depth=4),
    n_bootstrap=200,
    resampling="pairs",
    random_state=7,
)
method.fit(X_train, y_train)          # explicit model fitting happens here
estimate = method.estimate(X_test)    # prediction only; no refitting
\`\`\`

A factory should capture fixed hyperparameters. Do not tune hyperparameters on
the bootstrap samples unless that tuning procedure is itself part of the
predeclared method being compared.

## Resampling modes

- **pairs**: sample row indices with replacement and fit on the sampled
  \`(X, y)\` pairs. Appropriate for approximately exchangeable observations.
- **residual**: fit one reference model on the supplied training data, center
  its in-sample residuals, resample those residuals, and fit each replicate to
  \`(X, fitted_y + resampled_residual)\`. This is a fixed-design residual
  bootstrap; its validity depends on the residual/noise assumptions.
- **block**: sample contiguous blocks of row positions with replacement and
  truncate to the original row count. Set \`block_size\`; rows must already be
  ordered along the dependence axis. This is a simple moving-block scheme,
  not a general grouped, spatial, panel, or circular bootstrap.

For block resampling, select a block length appropriate to the dependence
structure before evaluating held-out results. The implementation does not
infer ordering or block length.

## Output semantics and limitations

The returned \`mean\`, \`scale\`, \`samples\`, and percentile bounds summarize the
bootstrap distribution of fitted model predictions. The bounds represent
sampling uncertainty in the fitted conditional-mean prediction. They are **not**
automatically calibrated prediction intervals for a future observation and
do not add irreducible observation noise. Use a separate, justified residual
or conformal predictive layer when total predictive uncertainty is required.

Percentile bounds are not guaranteed to achieve nominal coverage, especially
under model misspecification, small samples, dependence, heteroscedasticity,
or extrapolation/distribution shift. Bootstrap resampling does not repair
support gaps or justify extrapolation.

## Reproducibility and validation

Set \`random_state\` to an integer for deterministic resampling. The fitted
adapter retains the row indices selected for each replicate and reports the
resampling mode, block size, seed, and replicate count in diagnostics/metadata.
The method validates finite aligned arrays and every replicate's predictions.
No experiments, benchmark jobs, hyperparameter search, or LLM calls are
launched by this module.
