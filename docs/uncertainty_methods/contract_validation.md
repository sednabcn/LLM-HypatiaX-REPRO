# Automated uncertainty-method contract validation

The shared contract validators provide a common, side-effect-free check for
outputs produced by uncertainty estimators and calibration methods. They are
intended for method unit tests, adapter tests, and offline validation of stored
or fixture predictions.

## Public API

~~~python
from hypatiax.tools.uncertainty_methods import (
    validate_uncertainty_method_contract,
    validate_calibration_method_contract,
)
~~~

### Estimator outputs

~~~python
report = validate_uncertainty_method_contract(
    method=estimator,
    X=X_evaluation,
    estimates={
        0.90: estimate_at_90,
        0.95: estimate_at_95,
    },
)
~~~

Checks:
- estimator is an instance of the shared `UncertaintyMethod` contract;
- method name/version and capability declarations are valid;
- metadata and diagnostics are mappings;
- each nominal coverage is strictly between zero and one;
- each output is an `UncertaintyEstimate` aligned to the number of input rows;
- the estimate's existing shape, finite-value, scale, quantile, sample, and
  interval-bound rules pass `UncertaintyEstimate.validate`.

### Calibration outputs

~~~python
report = validate_calibration_method_contract(
    method=calibrator,
    calibrated_estimates={0.90: calibrated_90, 0.95: calibrated_95},
    n_samples=len(X_evaluation),
)
~~~

Checks:
- calibrator implements `CalibrationMethod`;
- metadata is a mapping;
- coverage keys are valid;
- outputs are aligned `UncertaintyEstimate` instances;
- each calibrated output includes valid lower and upper interval bounds.

## Important execution boundary

The validators do **not** call `fit()`, `estimate()`, `apply()`, train a
predictor, or perform calibration. The caller explicitly supplies outputs that
have already been computed. This keeps validation deterministic and prevents
hidden training, API calls, or costly inference.

The calibration validator cannot prove that `apply()` did not mutate its
input, or that calibration data were disjoint from training/test data. Those
properties require tests around the concrete calibrator and the split
provenance. Use `validate_split_indices` for row-level overlap checks and
group/time-aware splitters for dependent data.

## Recommended method test pattern

Each implementation should include:
1. a small deterministic fixture with fixed inputs and already-fitted or
   explicitly supplied model components;
2. one or more nominal coverage outputs (for example 0.80, 0.90, 0.95);
3. a call to the relevant contract validator;
4. invalid-input tests for row-count mismatch, NaN/Inf, malformed intervals,
   and unsupported outputs;
5. tests for method-specific assumptions (posterior diagnostics, ensemble
   member count, bootstrap unit, quantile crossing, or shift-weight overlap);
6. separate tests proving data-role separation and no unintended mutation.

The shared validator checks structure, not scientific validity. It does not
prove calibration, coverage guarantees, posterior convergence, ensemble
diversity, bootstrap validity, shift robustness, or extrapolation performance.
Those require method-specific statistical tests and evaluation on appropriately
separated data.

## Example pytest contract test

~~~python
def test_my_method_obeys_shared_contract():
    method = MyMethod(preconfigured_components=fixture_components)
    # Fixture output avoids fitting or inference during this contract check.
    estimates = {
        0.90: UncertaintyEstimate(
            mean=[1.0, 2.0],
            lower=[0.0, 1.0],
            upper=[2.0, 3.0],
        )
    }
    report = validate_uncertainty_method_contract(
        method, X=[[0.1], [0.2]], estimates=estimates
    )
    assert report["status"] == "ok"
~~~

## Scope

This change adds generic structural validation and tests only. It does not
register or implement any estimator, calibrator, method-specific algorithm,
cross-validation runner, benchmark, experiment, or LLM workflow.
