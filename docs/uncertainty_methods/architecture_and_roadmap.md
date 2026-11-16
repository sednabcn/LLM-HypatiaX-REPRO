# Uncertainty methods: architecture and roadmap

## Design principles

- One output contract, multiple estimators.
- Estimation and calibration are separate stages.
- Interval semantics and assumptions are explicit.
- Unsupported values are null/absent, not zero.
- Every result preserves method, domain, direction, distance, and coverage.
- Infrastructure never launches experiments, training jobs, benchmarks, or LLM requests implicitly.

## Architecture

\`\`\`text
Data split and provenance
        |
        v
UncertaintyMethod (fit -> estimate)
        |
        v
UncertaintyEstimate
        |
        +--------------------+
        |                    |
        v                    v
CalibrationMethod       Diagnostics
        |                    |
        +---------+----------+
                  v
             Evaluation
                  |
                  v
       UncertaintyResult / JSON
                  |
                  v
       Existing horizon curves
\`\`\`

The estimator layer is independent of Feynman adapters and horizon generation.
A future horizon adapter should simply call the common estimate interface for
each existing scenario and retain scenario provenance.

## Recommended lifecycle

1. Define training, validation, calibration, in-domain test, boundary test,
   and extra-domain test roles before fitting.
2. Fit constituent predictors on training data only.
3. Select methods/settings using validation only.
4. Calibrate on a separate calibration split where required.
5. Freeze all choices.
6. Estimate on untouched evaluation slices.
7. Evaluate point metrics, interval coverage/width, and diagnostics separately
   by domain, direction, distance, and nominal level.
8. Export versioned records with assumptions and split provenance.

Use blocked, grouped, temporal, or spatial splits where observations are
dependent; do not presume random exchangeability.

## Method implementation status

| Module | Status | Intended role / caveat |
|---|---|---|
| \`ensemble.py\` | Implemented | Adapts supplied fitted members; disagreement is not automatically calibrated |
| \`bootstrap.py\` | Implemented | Explicit factory-based pairs, residual, and moving-block resampling; percentile bounds quantify fitted-mean sampling spread, not calibrated future-observation intervals |
| \`bayesian.py\` | Planned | Posterior and posterior-predictive summaries; credible intervals depend on model and prior |
| \`quantile.py\` | Planned | Conditional quantile predictions; check quantile crossing and tail extrapolation |
| \`shift_aware.py\` | Planned | Weighted/local/group calibration; requires assumptions and support overlap |
| \`calibration.py\` | Partial | Split-conformal baseline exists separately; calibration adapters remain extensible |

## Implementation phases

- **Phase 0:** contracts, estimate container, registries, evaluation, JSON schema,
  documentation, and side-effect-free contract validators.
- **Phase 1:** adapters for supplied fitted ensembles and explicit bootstrap
  resampling; next, quantile adapter with common contract tests.
- **Phase 2:** Bayesian linear/GP adapters and posterior-predictive summaries.
- **Phase 3:** weighted/local/group conformal with effective sample size,
  overlap, and support diagnostics.
- **Phase 4:** integrate estimates with existing horizon scenarios and compare
  coverage/width against distance.

## Acceptance criteria for future methods

Each method PR should implement the common contract; document capability and
interval semantics; preserve data separation; expose assumptions and guarantee
scope; handle invalid/missing outputs explicitly; emit schema-compatible
records; include deterministic offline tests where possible; and avoid hidden
fitting, tuning, or expensive jobs during reporting.

## Non-goals of the ensemble adapter

The ensemble adapter does not train or refit constituent predictors, select
members, calibrate empirical spread, construct confidence intervals, or
orchestrate horizon experiments. The supplied split-conformal baseline remains
a separate calibration stage.

## Bootstrap-specific safeguards

Bootstrap fitting is explicit and factory-based. Pairs resampling assumes
row-level exchangeability; residual resampling assumes a defensible fixed-design
residual model; moving-block resampling assumes rows are pre-ordered and uses
contiguous blocks only. The adapter's percentile intervals describe model
sampling variability and do not include future observation noise or provide
extrapolation coverage guarantees.
