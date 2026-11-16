# Shared uncertainty-method infrastructure

## Purpose and scope

This package is the common foundation for future uncertainty methods in
HypatiaX. It is deliberately method-agnostic: Bayesian inference, ensembles,
bootstrap, quantile regression, and distribution-shift-aware calibration are
future extensions, not implemented estimators in this change.

The existing `hypatiax.tools.uncertainty` module remains the split-conformal
baseline and interval evaluator. This package adds reusable contracts around
future methods without replacing that API.

## Package map

- `base.py`: estimator/calibrator interfaces and `UncertaintyEstimate`.
- `registry.py`: explicit factory registries.
- `evaluation.py`: method-independent point and interval evaluation.
- `results.py`: versioned JSON-safe result records and export.
- `__init__.py`: public exports.

## Estimator contract

```python
from hypatiax.tools.uncertainty_methods import UncertaintyEstimate, UncertaintyMethod

class MyMethod(UncertaintyMethod):
    name = "my_method"
    version = "0.1"
    capabilities = frozenset({"mean", "scale", "samples", "interval"})

    def fit(self, X_train, y_train, **kwargs):
        # Fit on training data only. Never inspect calibration/test targets.
        self.model_ = ...
        return self

    def estimate(self, X, nominal_coverage=0.95, **kwargs):
        # Return one aligned estimate for every row of X.
        return UncertaintyEstimate(mean=..., scale=..., lower=..., upper=...)
```

For an adapter around an already-fitted predictor, `fit` may validate and
attach the predictor without refitting it; document that behavior explicitly.

### Estimate fields

| Field | Meaning |
|---|---|
| `mean` | Predictive mean or point estimate |
| `scale` | Non-negative predictive scale; document whether it is standard deviation |
| `lower`, `upper` | Paired interval bounds |
| `quantiles` | Probability level to predictive quantile |
| `samples` | Predictive draws, shape `(n_observations, n_draws)` |
| `components` | Named components, e.g. epistemic/aleatoric only when justified |
| `diagnostics` | Convergence, support, health, or shift diagnostics |
| `metadata` | Semantics, assumptions, and provenance |

Unsupported values remain `None` or absent, never zero. A scale alone is not
a prediction interval, and this library never silently converts scale to
bounds. Credible intervals, confidence intervals for a conditional mean, and
prediction intervals must retain explicit semantics in metadata.

## Separate calibration stage

`CalibrationMethod` consumes estimates and targets from a disjoint
calibration split, then transforms estimates for new inputs. It must not refit
the predictive model. Its metadata must describe calibration sample count,
score definition, nominal level, assumptions, guarantee scope, and support
diagnostics.

The existing `SplitConformalRegressor` is available from `hypatiax.tools`.
Ordinary split conformal relies on exchangeability; it does not guarantee
coverage under arbitrary extrapolation or distribution shift.

## Registry

```python
from hypatiax.tools.uncertainty_methods import UNCERTAINTY_METHODS
UNCERTAINTY_METHODS.register("my_method", MyMethod)
method = UNCERTAINTY_METHODS.create("my_method", option=True)
print(UNCERTAINTY_METHODS.names())
```

Registration is explicit and process-local. Importing this package does not
auto-discover plugins or execute model code. Duplicate names fail loudly.

## Evaluation and results

`evaluate_estimate(y_true, estimate, nominal_coverage=0.95)` reports MAE,
RMSE, bias, and R² when a mean is supplied. It reports empirical coverage and
mean width only when paired bounds are supplied. It does not calibrate and
does not infer intervals from scale. Undefined R² (constant evaluation
targets) is `None`, not zero.

`UncertaintyResult` represents one method × evaluation slice × optional
coverage level. It preserves equation/dataset, domain, horizon strategy,
direction, distance, point and interval metrics, uncertainty summaries,
calibration metadata, shift diagnostics, status, and reason.
`write_uncertainty_results_json(records, path)` writes a versioned document.
Non-finite floats become JSON null; missing values are not misreported as zero.

## Data separation and scientific safeguards

1. Training: model parameters and preprocessing.
2. Validation: model/method selection.
3. Calibration: interval calibration only.
4. In-domain test: held-out evaluation.
5. Boundary and extra-domain test: untouched horizon evaluation.

Never use extra-domain targets to select methods, tune hyperparameters, or
calibrate intervals and then report the same points as independent evaluation.
Learned scaling, density models, shift detectors, and importance weights must
obey the same split discipline.

Coverage outside the calibration distribution is an empirical diagnostic, not
a distribution-free guarantee. Covariate-shift weighting requires assumptions
such as stable conditional outcomes and adequate support overlap; it cannot
manufacture information where calibration support is absent.
