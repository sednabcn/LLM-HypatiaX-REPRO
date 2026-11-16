# Extrapolation: concepts, evaluation designs, metrics, and uncertainty

## 1. Purpose and scope

This guide is the conceptual and methodological reference for extrapolation work in
HypatiaX. It consolidates terminology, ways to define the evaluation domain, horizon
construction, point-prediction metrics, uncertainty and prediction intervals,
calibration, result schemas, leakage controls, and reporting requirements.

The goal is not merely to produce a score outside the training data. The goal is to
answer, reproducibly:

1. What does "outside the training domain" mean for this problem?
2. How far outside is each evaluation point, and in which direction?
3. How accurate are predictions at each distance?
4. How does predictive uncertainty change, and are intervals calibrated?
5. At what horizon does performance or reliability cease to meet a predeclared
   requirement?
6. Can the same protocol be reused for different equations, datasets, model families,
   and scientific domains?

The three mechanics equations currently used by the Feynman adapter are examples,
not the scope of the general framework. The generic horizon engine must remain
independent of any fixed equation list.

## 2. Terminology: interpolation, in-domain generalization, and extrapolation

These terms must be defined relative to the information available during fitting.

- **Training domain**: the support or region represented by the training inputs,
  together with the sampling design used to obtain them.
- **Intra-domain evaluation**: evaluation on unseen observations that remain within
  the declared training domain. This is often called interpolation, although
  interpolation can still be difficult in sparse or high-dimensional regions.
- **Boundary evaluation**: evaluation near the edge of the training domain. Report it
  separately when possible; it is not automatically equivalent to either ordinary
  interpolation or long-range extrapolation.
- **Extra-domain evaluation**: evaluation outside the declared training domain.
- **Extrapolation horizon**: a quantified distance from the training domain, measured
  using a stated metric and direction.
- **Distribution shift**: a change between training and evaluation distributions.
  Covariate shift, label/conditional shift, and changes in the physical mechanism are
  distinct situations. Extrapolation is often a form of covariate shift, but not every
  distribution shift is geometric extrapolation.
- **Support violation**: an evaluation point lies outside the support represented by
  training inputs. In continuous problems, finite samples only approximate support;
  the chosen operational definition must therefore be documented.

Do not label a test set "extrapolation" merely because it was collected later or held
out. State the domain rule that makes it extra-domain.

## 3. Ways to define the training domain

There is no universally correct domain representation. Choose one that matches the
problem and report its assumptions.

### 3.1 Univariate interval

For one feature with training minimum and maximum, the observed interval is
[x_min, x_max].

- Intra-domain: x_min <= x <= x_max.
- Upper extrapolation: x > x_max.
- Lower extrapolation: x < x_min.

A sample range is not a guarantee that every point inside it is well represented.
Density gaps and sparse tails should also be inspected.

### 3.2 Per-feature bounding box

For d features, the axis-aligned box is the product of each feature's observed
minimum/maximum interval. It is simple and interpretable, but may label impossible
combinations as in-domain. For example, each mass and radius can be individually
within range while their joint combination is far from all training observations.

### 3.3 Convex hull and geometric support

The convex hull captures the smallest convex region containing the training inputs.
Distance to the hull can measure how far a point lies outside that region. This is
more joint-feature-aware than a box, but can be computationally difficult and can
still include scientifically implausible regions when the true domain is non-convex.

Alternatives include alpha shapes, local density/support estimates, nearest-neighbour
distance, one-class models, and domain-specific feasible sets. These methods answer
different questions and should not be treated as interchangeable.

### 3.4 Standardised or whitened feature space

Raw Euclidean distance is dominated by features with large numerical scales. Common
choices are:

- Standardised Euclidean distance using training-set means and standard deviations.
- Robust scaling using training medians and interquartile ranges.
- Mahalanobis distance using a training-estimated covariance matrix.
- A domain-specific metric with scientifically meaningful feature weights.

All transforms and covariance estimates must be learned from training data only.
Handle constant, collinear, and highly correlated features explicitly.

### 3.5 Physical, constrained, and transformed domains

The mathematically possible region may differ from the physically admissible region.
Specify constraints such as positivity, conservation laws, bounds, monotonicity,
stability, or valid parameter combinations.

For positive variables spanning orders of magnitude, distances in log space may be
more meaningful than raw distances. For angular or periodic variables, use circular
distance rather than ordinary subtraction. For periodic signals, report phase and
frequency assumptions; a distance measured in periods is meaningful only when the
period is known or independently estimated without using extrapolation test outcomes.

### 3.6 Direction-aware multivariate domain

A multivariate point can leave the training domain in many directions. Evaluate
explicit, scientifically meaningful paths, for example:

- one feature increases while others remain fixed;
- one feature decreases;
- several features increase together;
- one feature increases while another decreases;
- radial paths away from a reference point;
- paths along physically constrained manifolds;
- paths toward and away from known singularities or regime boundaries.

Holding all other features at their training medians is useful for controlled
one-feature sensitivity, but it does not represent all interactions. Include
combination directions when interactions matter.

## 4. Ways to measure extrapolation distance and horizon

Always record the distance definition, units, reference boundary, direction, and
feature scaling. A number such as "distance = 1" is uninterpretable without them.

### 4.1 Training-range-width distance

For a one-dimensional upper-side test point:

d_upper = (x_test - x_max) / (x_max - x_min)

For a lower-side point:

d_lower = (x_min - x_test) / (x_max - x_min)

Thus 0 is the boundary, 0.5 is half a training-range width beyond it, and 1 is one
training-range width beyond it. This is intuitive for individual features but does
not solve multivariate geometry by itself.

### 4.2 Standardised boundary distance

Measure distance in training-standard-deviation units, or robust scale units. State
whether the scale is standard deviation, IQR, median absolute deviation, or another
quantity. This is useful when features have different units.

### 4.3 Nearest-training-point distance

For each evaluation point, compute its distance to the nearest training input in the
chosen scaled metric. This captures local sparsity but does not directly measure
distance beyond the outer boundary.

### 4.4 Distance to a domain boundary

For a declared support region S, use the shortest distance from a test point to S.
For points outside S, this gives a direct geometric extrapolation distance. The
distance metric and algorithm used to define S must be included in provenance.

### 4.5 Mahalanobis distance

Use the training mean and covariance to measure multivariate distance. This accounts
for feature correlations under its assumptions. It is not a universal support test:
a Gaussian-like ellipsoid can be misleading for nonlinear, multimodal, or constrained
domains.

### 4.6 Directional horizon ladder

A useful initial ladder is 0.25x, 0.5x, 1x, 2x, and 4x the relevant training-range
width. It is an experimental design, not a universal scale or a promise that every
horizon is physically valid. Add denser horizons near a performance or coverage
transition. Use separate upper, lower, and multivariate direction curves.

### 4.7 Horizon as a path, not just a scalar

For multivariate problems, a horizon record should identify the path or direction,
not only a scalar distance. Two points at the same distance can have very different
difficulty if they move along different directions or approach different physical
regimes.

## 5. Evaluation design: intra, boundary, and extra

Use disjoint evaluation sets and preserve their roles:

1. **Training set**: used to fit model parameters and preprocessing.
2. **Model-selection/validation set**: used for hyperparameter or model selection,
   with a documented sampling design.
3. **Calibration set**: used to calibrate uncertainty intervals when required.
4. **Intra-domain test set**: held out and sampled within the declared domain.
5. **Boundary test set**: held out near the boundary.
6. **Extra-domain test sets**: held out at predeclared distances and directions.

For small scientific datasets, nested or cross-validation designs may be needed.
However, random cross-validation alone can conceal extrapolation because folds may
share nearly identical input regions. Consider blocked, grouped, temporal, spatial,
parameter-regime, or leave-region-out splits that reflect the intended deployment.

For synthetic equations with known ground truth, generate evaluation inputs from the
declared design and calculate targets from the known function. This tests functional
generalisation under controlled conditions. Also test noisy observations and realistic
measurement processes where relevant; perfect synthetic equations do not establish
robustness to real-world noise or model misspecification.

For real observations, use untouched observed targets at each horizon. Never replace
unavailable observations with the known equation or expected answer unless the task
is explicitly a synthetic oracle evaluation.

## 6. Point-prediction metrics

No single metric is sufficient. Report complementary metrics and their domains.

### 6.1 R-squared

R² = 1 - sum((y - y_hat)^2) / sum((y - mean(y))^2)

R² compares squared prediction error with a constant-mean baseline on the evaluation
set. It can be negative; negative values are valid and must not be clipped or converted
to missing values. R² is undefined when evaluation targets have zero variance. R²
values across different horizons can be difficult to compare when target variance
changes substantially.

### 6.2 Mean absolute error

MAE = mean(abs(y - y_hat))

MAE is interpretable in target units and less sensitive to large residuals than RMSE.

### 6.3 Root mean squared error

RMSE = sqrt(mean((y - y_hat)^2))

RMSE penalises large errors more strongly and remains in target units. Report it with
the target scale and, where useful, a normalised counterpart.

### 6.4 Normalised RMSE

Possible denominators include training-target standard deviation, training-target
range, evaluation-target range, or a domain-specific physical scale. These definitions
are not equivalent. For cross-horizon comparisons, prefer a fixed denominator
calculated from training data, and name the denominator in the metric field. If the
training scale is zero or undefined, report the metric as undefined with a reason.

### 6.5 Mean absolute percentage error and percentage error

Percentage metrics are unstable or undefined near zero targets and can overweight
small denominators. State zero handling and whether the metric is symmetric.
Do not use an unexplained label such as "error_pct".

In the existing Exp2 far-scoring work, far/train RMSE ratio percentage means
100 * RMSE_far / RMSE_train. It is not MAPE and is not a per-observation percentage
prediction error. It is undefined when training RMSE is zero. Keep its name explicit.

### 6.6 Median absolute error, maximum error, and quantiles

Median absolute error describes typical residual magnitude robustly. Maximum absolute
error and high residual quantiles expose catastrophic tails. Report them when safety,
scientific constraints, or worst-case behaviour matter.

### 6.7 Directional and subgroup metrics

Report scores by horizon, direction, feature path, regime, and relevant subgroup.
Aggregate scores can hide a failure in one extrapolation direction. Do not pool
different equations or target scales without an explicit normalisation and aggregation
policy.

### 6.8 Metric coverage versus metric quality

Report separately:
- expected method/equation/direction/horizon outcomes;
- number with valid predictions;
- number with valid R²;
- number with valid RMSE;
- number with valid intervals and coverage metrics;
- failure or unsupported reasons;
- actual metric values.

A negative R² is a computed poor score, not a missing score. Unsupported methods,
missing predictors, invalid predictions, and metric-specific undefined cases are
different states.

## 7. Uncertainty: why it is central to intra/extra evaluation

Point accuracy alone does not show whether a model knows when it is unreliable.
Extrapolation can increase uncertainty, but a model may also remain confidently wrong.
Therefore uncertainty estimates and their empirical calibration must be evaluated
alongside point metrics.

Distinguish:

- **Confidence interval for a mean/parameter**: uncertainty about an estimated
  population quantity or conditional mean.
- **Prediction interval**: uncertainty for a future individual observation. It
  generally includes observation noise and is wider than a confidence interval for
  the mean.
- **Credible interval**: Bayesian posterior probability statement conditional on
  model and prior assumptions.
- **Prediction set/region**: a general set-valued predictive output, possibly
  non-parametric or multivariate.

Do not call every pair of lower/upper predictive bounds a confidence interval. Record
what quantity the interval covers.

### 7.1 Aleatoric uncertainty

Irreducible or observation-process uncertainty, such as measurement noise or
stochastic outcomes. It may be constant or heteroscedastic (varying with inputs).

### 7.2 Epistemic uncertainty

Uncertainty due to limited data, uncertain parameters, or model knowledge. It can
often decrease with informative additional training data, but extrapolation estimates
are model-dependent.

### 7.3 Model-form and structural uncertainty

Uncertainty from choosing an inadequate functional family, missing mechanisms,
incorrect constraints, or omitted variables. This is especially important in
scientific extrapolation and is not guaranteed to be captured by a single model's
predictive interval.

### 7.4 Extrapolation-related uncertainty

There is not always a uniquely identifiable additive "extrapolation uncertainty"
component. Treat it as a phenomenon to diagnose through horizon-dependent interval
width, calibration, model disagreement, sensitivity, and domain-distance analyses.
Do not claim a clean decomposition unless the estimator and assumptions support it.

## 8. Ways to estimate predictive uncertainty

Different methods quantify different uncertainty sources and make different
assumptions. Compare them rather than treating them as interchangeable.

### 8.1 Parametric predictive distributions

Fit a model that returns a predictive mean and variance or distribution parameters.
Check distributional assumptions, heteroscedasticity, residual diagnostics, and tail
behaviour. A parametric interval can be narrow and wrong under model misspecification.

### 8.2 Bayesian methods

Bayesian regression, Gaussian processes, Bayesian neural networks, and posterior
sampling can provide uncertainty conditional on the model and prior. Prior sensitivity
and out-of-domain behaviour must be assessed; posterior uncertainty does not
automatically account for model misspecification.

### 8.3 Ensembles and model disagreement

Train multiple independently initialised or otherwise varied models using only
permitted training data. Disagreement can serve as an epistemic uncertainty proxy.
An ensemble of similarly misspecified models can agree and still be wrong. Record
ensemble construction and spread definition.

### 8.4 Bootstrap

Resample training observations or groups, refit models, and examine predictive
variation. Resampling must respect dependence, groups, time, and experimental design.
Bootstrap intervals do not automatically remain calibrated under extrapolation.

### 8.5 Quantile regression

Estimate conditional quantiles directly. Check quantile crossing, sample size, and
coverage at each horizon. Quantile estimates can be unstable where training support
is sparse.

### 8.6 Conformal prediction

Conformal methods calibrate prediction sets using a calibration sample and can provide
finite-sample marginal coverage under exchangeability between calibration and test
examples. Ordinary split conformal guarantees do not automatically survive
distribution shift or extrapolation, where exchangeability is violated. Report the
calibration design, nominal level, calibration sample size, and the assumptions under
which any coverage claim is made. Weighted, local, covariate-shift, or adaptive
variants require their own assumptions and validation.

### 8.7 Sensitivity and scenario uncertainty

Vary uncertain inputs, parameters, boundary definitions, or plausible model choices.
This is useful for scientific robustness but is not automatically a probabilistic
prediction interval. Label scenario envelopes as such.

## 9. Interval metrics and calibration diagnostics

For lower and upper bounds L_i and U_i, with L_i <= U_i:

### 9.1 Empirical coverage

Coverage = mean( L_i <= y_i <= U_i )

Compare observed coverage with the nominal target (for example, 90% or 95%).
Report sample count and uncertainty around the coverage estimate. Small test sets
produce noisy coverage estimates.

### 9.2 Mean and normalised interval width

Mean width = mean(U_i - L_i)

Normalise by a fixed training target scale when comparing different targets or
equations. Always report the raw width too.

### 9.3 Calibration error

A simple absolute coverage gap is |empirical coverage - nominal coverage|. More
complete calibration analysis evaluates multiple nominal levels and compares the
empirical coverage curve with the identity line. State the aggregation and weighting
policy.

### 9.4 Sharpness

Narrower intervals are sharper, but sharpness is meaningful only subject to adequate
coverage. Do not reward narrow intervals that miss the true outcomes.

### 9.5 Proper scoring rules

Where full predictive distributions are available, consider negative log predictive
density, CRPS, interval score, or weighted interval score. These reward calibrated
and informative distributions under their definitions. State distribution support
and handling of invalid densities or tails.

### 9.6 Conditional and horizon-wise calibration

Compute coverage separately for:
- intra-domain;
- boundary;
- each extra-domain horizon;
- each direction/path;
- each method and equation;
- important target or input regimes.

A high pooled coverage can conceal severe undercoverage in far regions. Plot empirical
coverage against distance for several nominal levels, with sample counts or
uncertainty bands.

### 9.7 Coverage-accuracy trade-off

Report point error and interval quality together. A useful model comparison includes
far RMSE, normalised RMSE, nominal/empirical coverage, mean interval width, and a
proper score when available. Avoid selecting a model on interval width alone.

## 10. Calibration protocol and leakage prevention

Calibration is a learned step and must have its own data boundary.

1. Fit the model and preprocessing using the training split only.
2. Use a separate in-domain calibration split, or a documented cross-fitting
   procedure, to estimate interval calibration.
3. Freeze the model and calibration procedure before evaluating test sets.
4. Evaluate intra, boundary, and extra-domain test sets without using their targets
   to alter the intervals.
5. Report coverage by domain and horizon, including failures and sample counts.

If the deployment setting provides no representative calibration data for the
extrapolation region, do not tune intervals against the extra-domain test outcomes.
Instead report that calibration under shift is unverified, and evaluate the limitations
of the chosen uncertainty method. Recalibrating on extra-domain labels changes the
problem and must be described as a separate adaptation experiment.

For synthetic known-function tests, analytical truth may be used to score intervals,
but must not be used to tune the model or intervals if the purpose is to assess
generalisation. If the known function is used to construct the predictor, the test is
an oracle or symbolic-recovery test, not an independent black-box extrapolation test.

## 11. Choosing an acceptable extrapolation horizon

There is no universal maximum extrapolation distance. It depends on the function,
noise, sampling, feature geometry, physical constraints, model family, and intended
application.

Predefine acceptance thresholds for:
- maximum allowable RMSE or normalised RMSE;
- minimum R² if meaningful for the target distribution;
- minimum empirical interval coverage and acceptable calibration gap;
- maximum interval width or proper score;
- physical/domain constraint violations;
- minimum number of valid evaluation points;
- failure/unsupported-rate limits.

Then define the **reliable horizon** as the furthest tested distance along a specified
path for which all required criteria are satisfied. Do not report one global horizon
when different directions or methods have different limits. Interpolate between tested
distances only with a clearly stated procedure; otherwise report the furthest tested
passing distance, not an unmeasured exact threshold.

## 12. General result schema

Every record should be self-describing and machine-readable. Suggested fields:

```json
{
  "schema_version": "2.0",
  "project": "project_id",
  "equation_or_task": "task_id",
  "method": "method_id",
  "split": "extra_test",
  "domain_status": "extra",
  "distance": {
    "value": 1.0,
    "definition": "training_range_width",
    "units": "range_widths",
    "direction": [1, -1],
    "features_moved": ["feature_a", "feature_b"]
  },
  "sample_counts": {
    "expected": 120,
    "valid_predictions": 120,
    "valid_intervals": 120
  },
  "point_metrics": {
    "r2": -0.12,
    "mae": 0.08,
    "rmse": 0.11,
    "normalised_rmse": 0.14,
    "normalisation": "training_target_std"
  },
  "uncertainty": {
    "kind": "prediction_interval",
    "nominal_coverage": 0.95,
    "empirical_coverage": 0.72,
    "mean_width": 0.31,
    "normalised_mean_width": 0.39,
    "absolute_coverage_gap": 0.23,
    "calibration_method": "method_and_version",
    "calibration_split": "in_domain_calibration",
    "status": "undercovered"
  },
  "diagnostics": {
    "prediction_status": "scored",
    "interval_status": "scored",
    "failure_reason": null
  },
  "provenance": {
    "commit": "commit_sha",
    "config_hash": "config_hash",
    "training_split_id": "split_id",
    "calibration_split_id": "calibration_id",
    "model_retrained_on_extra": false,
    "extra_targets_used_for_calibration": false
  }
}
```

This is a proposed cross-project schema, not a claim that every field is currently
implemented by the existing tools. Keep metric values null only with a specific
status/reason. Preserve coverage counts and diagnostic details.

## 13. Curves and visual reporting

For each method and task, produce separate curves against distance:

1. R² (with caveat when target variance changes).
2. RMSE and training-scale-normalised RMSE.
3. MAE or robust error quantiles.
4. Empirical interval coverage for each nominal level, plus nominal reference lines.
5. Mean and normalised interval width.
6. Calibration gap or proper predictive score.
7. Prediction failure/validity fraction.
8. Optional model disagreement or uncertainty decomposition.

Use separate panels or plots when metrics have incompatible units. Label direction,
feature path, domain status, sample count, nominal interval level, and distance
definition. Include intra-domain and boundary reference points. Do not aggregate
directional curves unless the aggregation rule is explicit.

## 14. Failure taxonomy and score availability

At minimum distinguish:

- unsupported method (no valid predictor/representation);
- formula missing or parse failure;
- formula-to-feature argument mismatch;
- predictor unavailable;
- preprocessing state unavailable;
- prediction exception;
- prediction shape mismatch;
- non-finite prediction;
- invalid physical/domain point;
- interval provider unavailable or failed;
- malformed interval bounds;
- metric undefined (for example, zero target variance for R²);
- metric computation failure.

Coverage and quality are separate. A method with a poor negative R² has a valid score.
A method with no predictor has no score. A method with valid RMSE but undefined R²
has partial metric coverage. Never collapse these cases into a single null or silently
suppress exceptions.

## 15. Reusable software architecture

The core horizon system should be domain-agnostic. A scalable architecture has:

### Generic horizon engine

Responsible for:
- receiving training data and a declared domain/distance strategy;
- generating or accepting evaluation points;
- tracking paths, directions, and distance metadata;
- invoking already-fitted predictors;
- invoking optional interval providers;
- computing metrics and diagnostics;
- serialising versioned records and plotting curves.

It must not fit, tune, or retrain models on far-region points.

### Domain/task adapter

Provides:
- feature names and units;
- domain constraints and valid-point checks;
- domain boundary/support logic where known;
- meaningful directions or paths;
- optional target/reference function for synthetic evaluation;
- metadata and provenance.

This adapter must be configurable or extensible; it must not restrict the framework to a fixed list of three equations.

### Method/predictor adapter

Provides:
- a callable for the already-fitted model;
- consistent preprocessing and feature ordering;
- optional uncertainty/interval callable;
- optional distribution or ensemble outputs;
- method-specific diagnostics.

### Calibration component

Provides a separately fitted or derived calibration object using an allowed
calibration split. It must identify the calibration method, data split, nominal level,
and assumptions. The generic scorer should not silently calibrate using test labels.

### Reporting/export layer

Provides:
- versioned JSON records;
- coverage summaries;
- per-method/per-task/per-direction curves;
- reproducibility metadata;
- explicit metric and interval status.

The current reusable tools in `hypatiax/tools/extrapolation_horizon.py` implement
scenario generation, point scoring, optional caller-supplied interval scoring, JSON
export, and plotting. The current Feynman adapter is a domain-specific example.
Current interval support evaluates supplied bounds; it does not itself provide a
universal uncertainty estimator or calibration algorithm.

## 16. Current repository references and limitations

Related implementation and methodology documents:

- `docs/extrapolation_horizon_tools.md`: generic horizon API, strategies, metrics,
  and safeguards.
- `docs/feynman_horizon_integration.md`: current mechanics adapter and its
  domain constraints.
- `docs/exp2_extrapolation_failure_resolution_methodology.md`: diagnosis and
  repair of far-score failures, formula mapping, retained predictors, and coverage.
- `hypatiax/tools/extrapolation_horizon.py`: generic scenario and scoring code.
- `hypatiax/tools/feynman_horizon.py`: current Feynman-specific adapter.

Known limitations to keep visible:

1. Existing generic interval support accepts caller-supplied lower/upper bounds and
   computes empirical coverage and width; it does not estimate uncertainty.
2. It does not implement calibration, conformal prediction, Bayesian inference,
   ensembles, bootstrap, quantile regression, or distributional scoring automatically.
3. Coverage computed on synthetic reference-function values is not evidence of
   calibration on real noisy observations.
4. A single-feature ray with other features fixed at medians does not describe all
   multivariate paths.
5. Training-range distance is a useful baseline, not a universal multivariate support
   metric.
6. A nominal interval's calibration under distribution shift is not guaranteed.
7. The existing far/train RMSE ratio is undefined at zero training RMSE and must not
   be confused with percentage prediction error.
8. The current Feynman adapter covers three mechanics equations as examples only;
   generalisation requires configurable domain/task adapters and independent tests.

## 17. Recommended staged roadmap

### Stage A — documentation and schema

- Adopt shared terminology for intra, boundary, and extra domains.
- Define distance metadata and method/task/direction identifiers.
- Version a cross-project JSON schema.
- Keep point metrics, uncertainty metrics, and availability diagnostics separate.

### Stage B — domain-general horizon interface

- Accept arbitrary task adapters and domain constraints.
- Support axis-aligned, scaled, nearest-neighbour, hull-based, and caller-defined
  distance/support strategies where appropriate.
- Support explicit paths and directions.
- Test with multiple unrelated synthetic functions, not only mechanics equations.

### Stage C — uncertainty interface

- Standardise prediction interval and predictive-distribution interfaces.
- Record whether output is a confidence interval, prediction interval, credible
  interval, or prediction set.
- Support multiple nominal coverage levels.
- Add interval validity checks, coverage, width, calibration gaps, and proper scores
  where full distributions are available.

### Stage D — calibration and uncertainty methods

- Add calibration using a dedicated in-domain calibration split.
- Implement or integrate selected uncertainty estimators (for example, quantile
  regression, ensembles, bootstrap, or conformal methods) behind explicit adapters.
- Test under controlled covariate shift and known synthetic ground truth.
- Do not claim distribution-free extra-domain coverage without the assumptions that
  justify it.

### Stage E — scientific validation

- Test noisy and noiseless settings, feature interactions, nonlinearity, singularities,
  periodicity, physical constraints, and model misspecification.
- Compare intra, boundary, and extra performance for multiple methods.
- Report reliability horizons per direction and task.
- Run controlled scientific experiments only when explicitly authorised.

## 18. Minimum reporting checklist

For every extrapolation study, record:

- [ ] Scientific question and intended deployment use.
- [ ] Training domain definition and support assumptions.
- [ ] Training/validation/calibration/intra/boundary/extra split definitions.
- [ ] Feature transforms, scaling, units, constraints, and fit-data provenance.
- [ ] Distance metric, reference boundary, direction, and horizon units.
- [ ] Evaluation sample counts at every horizon.
- [ ] Predictor identity and confirmation that it was not refit on extra data.
- [ ] Point metrics with explicit normalisation.
- [ ] Uncertainty type and estimation method.
- [ ] Nominal levels, empirical coverage, interval width, and calibration protocol.
- [ ] Metric coverage and failure reasons.
- [ ] Per-method, per-task, per-direction result curves.
- [ ] Predeclared acceptance thresholds and reliable horizon.
- [ ] Commit, configuration, random seeds, artifacts, and known limitations.
- [ ] Clear distinction between unit/CI verification and scientific experiment evidence.

## 19. Interpretation principles

- A good intra-domain score does not imply good extrapolation.
- A good extra-domain point score at one distance does not imply reliability in
  another direction or at a longer horizon.
- A wide interval can be honest but uninformative; a narrow interval can be sharp but
  dangerously miscalibrated.
- Empirical coverage is a property of a specified evaluation sample and design, not
  a universal guarantee.
- Extrapolation uncertainty is especially sensitive to model-form assumptions.
- A benchmark's successful execution and metric coverage do not establish scientific
  validity.
- No single distance metric, point metric, or uncertainty method is universally best.
  The scientific domain and intended use determine the appropriate combination.

The central evaluation principle is therefore: **measure accuracy, uncertainty,
calibration, and failure coverage as functions of explicitly defined distance and
direction from the training domain.**
