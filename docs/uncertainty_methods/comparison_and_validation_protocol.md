# Uncertainty-method comparison and validation protocol

This protocol defines how future uncertainty estimators and calibration methods
are compared without giving one method privileged data, tuning access, or
evaluation conditions. It is a specification, not an experiment runner.
Nothing here launches training, benchmarks, model fitting, or LLM requests.

## 1. Preregister the comparison

Identify dataset/version, prediction task and target units, sample/group/time
identifiers, training-domain definition, evaluation domains, method/version/
configuration, split strategy and seed, nominal coverage, interval semantics,
and (for extrapolation) horizon geometry and distance.

Before fitting, record the primary selection metric, evaluation metrics,
coverage levels, split strategy, random seeds, method configurations, compute
budget, and rules for failed or unsupported outputs. Do not change these after
viewing test results. Exploratory changes require a new protocol version or
must be clearly marked exploratory.

## 2. Data roles and leakage prevention

| Role | Permitted use | Prohibited use |
|---|---|---|
| Train | Fit predictor and estimator; estimate training scale | Final selection |
| Validation | Select hyperparameters, architecture, stopping rules | Final calibration/reporting |
| Calibration | Fit a declared calibration map/radius after model selection | Predictor fitting or tuning |
| In-domain test | Final in-domain evaluation | Fitting, calibration, selection |
| Boundary / extra-domain test | Final shift and extrapolation evaluation | Fitting, calibration, selection |

Not every method needs a separate calibration split, but unused roles must be
marked explicitly. If data are scarce, use nested or cross-fitting designs and
document the construction; do not silently reuse test data.

Use group-, time-, spatial-, or block-aware splitting when observations are
dependent. Row-level disjointness is necessary but does not establish group-level
independence. Keep entities, repeated measurements, trajectories, and derived
observations from crossing roles where that would leak information.

The shared validate_split_indices helper checks non-empty one-dimensional
integer indices, bounds, duplicates, required roles, and row overlap. It does
not create splits or detect group/time leakage; callers must use an appropriate
splitter and retain group-level provenance.

## 3. Equal comparison conditions

1. **Same task and data:** every method sees the same training and evaluation
   rows for each seed and domain.
2. **Same predictor policy:** either compare uncertainty estimators around a
   common frozen predictor, or compare full predictive systems as a separate
   track. Do not mix the interpretations in one ranking.
3. **Same tuning budget:** equal validation access, declared search budget,
   stopping rule, and compute limits. Record wall time, memory where available,
   and failures/timeouts.
4. **Same calibration access:** methods receive the same calibration examples
   and target coverage levels. A method not requiring calibration records so.
5. **No test-driven choices:** no model, threshold, feature, interval, or
   calibration changes after test outcomes are inspected.
6. **Reproducibility:** record seeds, package versions, runtime context where
   relevant, and deterministic settings. Repeat all preregistered seeds; do not
   report only the best seed.

When method families have different training costs, report quality and resource
use. Provide a common-predictor track where possible to isolate uncertainty
quality from predictor quality.

## 4. Evaluation slices and extrapolation horizons

Report separately for in-domain test, boundary region, each extra-domain or
shift region, each declared direction and horizon distance, and each nominal
coverage level.

For extrapolation, define distance geometry before evaluation. For one feature,
distance in training-range widths from the nearest training boundary is useful.
For multivariate inputs, document scaling, direction vectors, feature
constraints, and whether distance uses rays, a norm, or a support/convex-hull
boundary. Use log-space for positive features spanning orders of magnitude
when scientifically justified. Do not treat different geometries as
interchangeable.

Use a fixed horizon ladder (for example 0.25, 0.5, 1, 2, and 4 training-range
widths) chosen before inspecting outcomes. Preserve the same fitted model and
preprocessing at every horizon. Never add horizon points to training or
calibration. For known periodic variables, report phase/period-aware distance
as well; do not infer periodic structure from numeric distance alone.

## 5. Required metrics

### Point prediction

When a predictive mean exists, report MAE, RMSE, bias, and R². Also report a
scale-normalized error such as RMSE divided by training-target standard
deviation, defining the denominator and its source. Do not calculate metrics
from unavailable outputs.

### Predictive intervals

For every nominal level (recommended: 80%, 90%, 95%), report empirical
coverage, mean interval width, interval score (with exact definition and
nominal level), absolute coverage gap, and evaluated sample count.

Report coverage and width together: coverage alone rewards arbitrarily wide
intervals. State whether intervals are central, equal-tailed, asymmetric, or
otherwise constructed. Distinguish prediction intervals for future outcomes
from confidence/credible intervals for a conditional mean or parameter.

For distributional predictions, report proper scores such as CRPS or log score
only when the method supplies the required distribution and scoring is
consistent. For quantile methods, report pinball loss per quantile and crossing
frequency. For ensembles, report member count and diversity diagnostics;
disagreement is not calibrated coverage. For Bayesian methods, report
convergence/effective-sample diagnostics and distinguish posterior from
posterior-predictive uncertainty. For bootstrap methods, report resampling unit
and scheme. For shift-aware methods, report weights, support/overlap diagnostics,
and effective sample size.

### Diagnostics and unavailable metrics

Preserve aleatoric/epistemic components, ensemble spread, posterior summaries,
calibration parameters, shift weights, effective sample size, warnings, and
failure reasons where available. Do not assume components are identifiable or
directly comparable across method families.

Use explicit status/reason fields for unsupported or undefined metrics:
missing predictive mean, no interval supplied, insufficient calibration size,
zero training-target scale, invalid prediction, or insufficient valid horizon
points. Never replace missing metrics with zero. Negative R² is valid and is
not a failure sentinel.

## 6. Calibration and uncertainty validity

Calibrate only after model/method selection, using the designated calibration
data. Record calibration method, sample count, exchangeability/dependence
assumptions, nominal coverage, and guarantee scope.

Empirical test coverage is a diagnostic, not a universal guarantee. Standard
split-conformal marginal coverage relies on exchangeability; it does not
automatically extend to extrapolation or arbitrary distribution shift. Weighted,
local, group-conditional, or shift-aware variants require their own assumptions
and diagnostics. Do not label a method calibrated under shift solely because
one shifted test set achieved nominal empirical coverage.

Report interval calibration separately for every domain and horizon. Aggregate
coverage can hide severe under-coverage in a direction or subgroup.

## 7. Repeated runs and statistical comparison

Use the same preregistered seeds/splits for all methods (paired comparison).
Report per-seed results, mean, standard deviation, and sample count; include
confidence intervals for aggregate differences when a defensible resampling
unit is available. Resample at the independent unit (subject, trajectory, or
time block), not individual correlated rows.

Do not interpret overlapping/non-overlapping confidence intervals as a
substitute for paired comparison. State the comparison estimand, uncertainty
method, and multiplicity handling when many methods, domains, horizons, or
coverage levels are compared. Keep exploratory subgroup analyses distinct
from preregistered primary outcomes.

## 8. Failure handling

A method run must end in one of: ok, partial, failed, or unsupported. Preserve
failure reason and diagnostics. Partial runs can contribute valid metrics, but
each missing metric remains explicitly missing. Do not silently drop failed
seeds or methods from summary tables; report denominators and failure counts.

## 9. Result schema and provenance

Use the shared UncertaintyResult and JSON writer for versioned, JSON-safe
records. Each record should represent one method × dataset × evaluation slice
× nominal coverage (where relevant) × seed. Include:

- dataset/task identifiers and split-manifest hash or immutable reference;
- method and implementation version/configuration;
- predictor identity/version and whether shared or method-specific;
- domain, direction, moved features, distance and distance units;
- nominal coverage and interval kind;
- metrics, sample count, status/reason, and diagnostics;
- seed, protocol version, software versions, and timestamp.

Store per-seed records as the source of truth. Derived summaries should retain
their aggregation method and source record identifiers. Avoid embedding raw
sensitive data in result files.

## 10. Acceptance checklist for method implementations

- [ ] Implements the shared UncertaintyMethod or CalibrationMethod contract.
- [ ] Declares capabilities, interval semantics, assumptions, and guarantee scope.
- [ ] Uses only permitted data roles; no implicit refit or test-driven calibration.
- [ ] Handles shape, NaN/Inf, degenerate targets, and insufficient samples.
- [ ] Emits schema-compatible results with explicit unavailable metrics.
- [ ] Has deterministic offline tests for core math and invalid inputs.
- [ ] Tests split leakage or data-role misuse where relevant.
- [ ] Reports method-specific diagnostics and computational cost.
- [ ] Documents unsupported settings and known failure modes.
- [ ] Does not launch experiments, training, benchmarks, or LLM calls implicitly.

## 11. Minimal example

~~~python
from hypatiax.tools.uncertainty_methods import (
    ComparisonProtocol,
    validate_split_indices,
)

protocol = ComparisonProtocol(
    split_strategy="group",
    seeds=(17, 29, 43),
    nominal_coverages=(0.80, 0.90, 0.95),
).validate()

splits = validate_split_indices(
    {
        "train": train_indices,
        "validation": validation_indices,
        "calibration": calibration_indices,
        "test": test_indices,
    },
    n_samples=len(dataset),
    required_roles=("train", "validation", "calibration", "test"),
)
~~~

This validates caller-supplied indices; it does not choose a group splitter,
fit a model, calibrate an interval, or run a comparison.

## 12. Scope and limitations

This infrastructure supplies protocol defaults and row-level split checks.
It does not implement split generation, nested cross-validation, group/time
leakage detection, metric aggregation, statistical hypothesis tests, resource
profiling, or uncertainty estimators. Those should be separate explicit
components with tests and documented assumptions.
