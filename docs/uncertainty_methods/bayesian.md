# Bayesian uncertainty methods

## Core idea

Bayesian methods represent uncertainty about unknown model parameters or
functions with a posterior distribution. Given training data D and parameters
theta, Bayes' rule gives p(theta | D) proportional to p(D | theta) p(theta).
Predictions integrate over this posterior rather than using only one fitted
parameter value.

For a regression model, distinguish:
- **Posterior over parameters/functions:** uncertainty about the latent model.
- **Posterior predictive distribution:** uncertainty about a future observation,
  integrating parameter uncertainty and (when modelled) observation noise.
- **Credible interval:** a posterior probability statement conditional on the
  model and prior. It is not automatically a frequentist confidence interval
  or a calibrated prediction interval under distribution shift.

## Candidate methods

- Bayesian linear regression: tractable baseline with explicit prior and noise model.
- Gaussian processes: posterior mean and variance with kernel-defined smoothness.
- Bayesian neural networks: flexible but inference and calibration can be difficult.
- Approximate inference: variational inference, Laplace approximation, or MCMC;
  document approximation quality and convergence.

## Assumptions and failure modes

Specify the likelihood, prior, model class, noise assumptions, and inference
method. Misspecified priors, likelihoods, kernels, and extrapolation behavior
can yield confident but incorrect predictions. GP uncertainty far from data
depends strongly on kernel and mean-function assumptions. Approximate posterior
inference can understate uncertainty.

For physical laws, encode known constraints only when justified and report
which constraints were imposed. Avoid treating a narrow posterior as evidence
that the functional form is correct.

## Required outputs and diagnostics

- Posterior draws or predictive draws, with shape and draw semantics documented.
- Predictive mean and quantiles/intervals at requested levels.
- Separate latent-function and observation-predictive uncertainty when available.
- Prior specification, likelihood, inference algorithm, convergence diagnostics,
  effective sample size where meaningful, and random seed.
- Sensitivity to prior/kernel/likelihood choices.

## Evaluation plan

Use synthetic functions with known parameters and noise. Check parameter
recovery, predictive log score or another proper scoring rule, interval
coverage/width in-domain, and behavior over increasing extrapolation distance.
Run misspecification controls (wrong functional form, heteroscedastic noise,
heavy tails). Evaluate observation prediction separately from latent-function
estimation.

## Template

See `hypatiax/tools/uncertainty_methods/templates/bayesian_template.py`.
The template is intentionally incomplete; select and document a specific
inference backend before implementing it.
