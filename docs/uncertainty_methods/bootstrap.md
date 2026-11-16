# Bootstrap uncertainty methods

## Core idea

Bootstrap methods approximate sampling variability by repeatedly resampling
the observed data and repeating a fitting or estimation procedure. The
distribution of replicate predictions can summarize sensitivity to the
training sample.

Bootstrap prediction spread is not automatically a prediction interval for a
future observation. To predict an individual outcome, account for observation
noise as well as model/sample variability, or calibrate the resulting interval.

## Resampling designs

- Pairs bootstrap: resample (X, y) rows; often unsuitable for fixed-design settings.
- Residual bootstrap: resample fitted residuals; depends on residual assumptions.
- Wild bootstrap: useful for some heteroscedastic settings.
- Block bootstrap: preserve temporal/spatial dependence by resampling blocks.
- Parametric bootstrap: simulate from an explicitly specified fitted model.

Choose the resampling unit to match the dependence structure. Do not randomly
shuffle correlated time-series observations and call the result valid.

## Assumptions and failure modes

Small samples, influential observations, model selection, heteroscedasticity,
heavy tails, and distribution shift can undermine bootstrap approximations.
Ordinary bootstrap resamples the empirical training support; it does not create
information in unobserved extrapolation regions. Record failed replicates and
do not silently discard them if failure is systematic.

## Required outputs and diagnostics

- Replicate predictions (n_observations × n_replicates).
- Resampling scheme, unit/block size, replicate count, seed, and fit failures.
- Mean/median, standard deviation, and empirical quantiles.
- Fraction of failed/non-finite replicates and convergence diagnostics.
- Whether predictions represent fitted-function variability or future outcomes.

## Evaluation plan

Use repeated synthetic datasets where the data-generating process is known.
Assess empirical coverage across repeated datasets, not only one test split.
Compare pairs/residual/wild/block variants when their assumptions differ.
Measure sensitivity to sample size, influential points, heteroscedasticity, and
extrapolation distance.

## Template

See `hypatiax/tools/uncertainty_methods/templates/bootstrap_template.py`.
The template separates resample generation, estimator fitting, and prediction
so that the resampling design can be reviewed independently.
