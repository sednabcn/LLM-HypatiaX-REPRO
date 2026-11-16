# Quantile-regression uncertainty estimator

\`QuantileRegressionUncertainty\` adapts independently fitted conditional
quantile regressors to the shared \`UncertaintyMethod\` interface.

## Configure quantile estimators

The caller supplies one factory per quantile level. Each factory should create
a fresh estimator configured with the appropriate quantile objective (for
example, pinball loss at that level). The adapter does not assume a particular
library or fit keyword convention.

\`\`\`python
from sklearn.ensemble import GradientBoostingRegressor
from hypatiax.tools.uncertainty_methods import QuantileRegressionUncertainty

levels = (0.05, 0.50, 0.95)
method = QuantileRegressionUncertainty({
    q: (lambda q=q: GradientBoostingRegressor(
        loss="quantile", alpha=q, n_estimators=150, max_depth=2,
    ))
    for q in levels
})
method.fit(X_train, y_train)  # explicit fitting, once per configured level
estimate = method.estimate(X_test, nominal_coverage=0.90)
\`\`\`

Construction and \`estimate()\` never fit models. \`fit()\` explicitly creates
and fits one estimator per configured quantile. Hyperparameters and model
selection should be fixed using training/validation roles before held-out
evaluation; do not tune on calibration or test domains.

## Interval construction

For nominal central coverage \(1-\\alpha\), the adapter uses the exact
conditional quantile levels \(\\alpha/2\) and \(1-\\alpha/2\). It only emits
\`lower\` and \`upper\` when both exact levels were configured and fitted.
It does not silently interpolate or substitute nearby levels. A median
(\`0.5\`) is exposed as the point \`mean\` when available; this is a conditional
median, not necessarily a conditional expectation.

## Quantile crossing

Quantile predictions should be non-decreasing with quantile level. The adapter
reports the number and fraction of evaluation rows with any crossing, plus
counts for each adjacent pair. It deliberately does not rearrange predictions
or hide crossings. If a downstream correction is chosen, document and apply it
as a separate, predeclared post-processing step, and evaluate its effect.

## Statistical interpretation and limitations

The bounds are central conditional-quantile intervals. They are not
automatically calibrated and have no distribution-free coverage guarantee.
Their empirical coverage can differ from nominal levels due to finite samples,
model misspecification, quantile crossing, heteroscedasticity, dependence, and
distribution shift. Extrapolation coverage is especially not guaranteed.
Quantile regression estimates conditional outcome quantiles, but validity
depends on the model, loss optimization, data support, and evaluation design.

A conditional median is not a predictive mean. The adapter does not return
synthetic predictive samples or infer a standard deviation from quantile
width. It does not add a conformal calibration stage; use the separate
calibration interface on a disjoint calibration split when appropriate.

## Reproducibility

The adapter records quantile levels, estimator count, and fitting lifecycle in
metadata/diagnostics. Reproducibility of the underlying model fits is the
responsibility of the supplied estimator factories and their random seeds.
No experiments, benchmarks, hyperparameter searches, or LLM calls are
launched by this module.
