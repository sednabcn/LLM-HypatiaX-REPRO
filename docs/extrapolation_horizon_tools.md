# Reusable extrapolation-horizon tools

The model-agnostic implementation lives in
`hypatiax/tools/extrapolation_horizon.py`. It generates evaluation regions,
scores already-produced predictions, exports JSON, and plots performance by
method and distance. It never fits or retrains a model.

## Public API

Import from `hypatiax.tools`:

- `generate_horizon_scenarios`: upper, lower, both, and multivariable
  combination directions.
- `evaluate_horizon_scenarios`: apply an existing predictor and optional
  interval provider to generated points, using a caller-supplied reference
  function for ground truth.
- `score_predictions`: score held-out predictions directly.
- `write_results_json`: write versioned, JSON-safe result records.
- `plot_horizon_curves`: plot a metric against distance, with separate
  curves for method, strategy, and moved features.

## Example

```python
import numpy as np
from hypatiax.tools import (
    generate_horizon_scenarios,
    evaluate_horizon_scenarios,
    write_results_json,
    plot_horizon_curves,
)

# X_train and y_train must be the actual in-domain training split.
scenarios = generate_horizon_scenarios(
    X_train,
    distances=(0.25, 0.5, 1.0, 2.0, 4.0),
    strategy="both",
    feature_names=("mass", "velocity"),
    n_points=120,
    periods={1: 2.0},  # Optional known period for feature index 1.
)

# model is already fitted. For synthetic data, reference_fn evaluates the
# known equation; for observed data, score held-out observations directly.
records = evaluate_horizon_scenarios(
    scenarios,
    predict_fn=model.predict,
    y_train=y_train,
    y_true_fn=reference_fn,
    train_predictions=model.predict(X_train),
    interval_fn=None,  # Or return (lower, upper) prediction bounds.
    method="MyMethod",
    equation="my_equation",
    base_function={"family": "harmonic", "frequencies": [1.0]},
)
write_results_json(records, "horizon_results.json")
plot_horizon_curves(records, "normalized_far_rmse", "horizon_rmse.png")
```

## Strategies and distance interpretation

Distances are multiples of the training range width for each moved feature.
Upper and lower scenarios move one feature at a time; the remaining features
are held at their training medians. Combination scenarios move several
features simultaneously using explicit -1/0/+1 direction vectors. This
supports mixed directions such as one feature above its maximum while another
is below its minimum.

For periodic or harmonic functions, supply known feature periods. The tool
reports distance in periods as additional metadata; it does not estimate
frequencies, phases, or a harmonic decomposition. Those properties belong in
the caller-provided `base_function` metadata.

## Metrics and uncertainty

The exporter records far R², far RMSE, normalized far RMSE (normalized by the
training-target standard deviation), and far/train RMSE ratio when its
denominator is non-zero. Prediction interval coverage and mean width are
computed only when both interval bounds are provided. Every metric has
independent availability diagnostics. A zero training RMSE makes the ratio
undefined; it does not invalidate far R², RMSE, or normalized RMSE.

The caller is responsible for supplying valid prediction intervals and
ground-truth values. Empirical interval coverage is not a guarantee of
calibration under distribution shift.

## Reproducibility and leakage controls

- Pass the exact training split, not the full dataset, as `X_train` and
  `y_train`.
- Fit feature scaling and model preprocessing on training data only.
- Reuse the same fitted model at every horizon; do not retrain on far points.
- Do not use generated far targets to fit, select, or calibrate the model.
- Record equation, base-function family, method, distance, moved features,
  sample count, and uncertainty status with each result.
- The generated one-feature rays hold other features at medians; for
  interaction-sensitive systems, use explicit multivariable directions and
  also evaluate realistic domain constraints.

The module requires NumPy. Matplotlib is imported only when plotting is
requested, so JSON export and scoring do not require it.
