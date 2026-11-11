# Core-295 source verification audit 34: Parkinson range variance, GARCH(1,1) and normal expected shortfall

**Date:** 2026-11-11  
**Status:** verification of discovery-batch 28 leads. Parkinson, Bollerslev and RiskMetrics sources are now registered as candidate_reference; no equation is added to the formal catalogue or counted toward 295.

## 1. Parkinson 1980 extreme-range variance estimator

### Primary transcription

Michael Parkinson, *The Extreme Value Method for Estimating the Variance of the Rate of Return*, Journal of Business 53(1) (1980), 61–65. The original article scan is accessible.

Parkinson models the log price as a one-dimensional continuous random walk with diffusion constant \(D\). For the range \(l=X_{\max}-X_{\min}\) over a unit interval, the paper derives:
\[
E[l^2]=4\ln(2)D.
\]
It then states the unit-interval estimator:
\[
\widehat D
=0.361\,E[l^2]
\]
and, for \(n\) observed unit intervals with \(l_i=\ln(H_i/L_i)\),
\[
\widehat D_P
=\frac{0.361}{n}\sum_{i=1}^{n}
\left[\ln\left(\frac{H_i}{L_i}\right)\right]^2.
\]
The coefficient \(0.361\) is the paper's rounded value of \(1/(4\ln2)\). The paper explicitly assumes a zero-drift random walk for the price logarithm and uses equally spaced observations.

### Validity and family boundary

The original paper's diffusion parameter \(D\) is the variance of log-price displacement over a unit interval. The range estimator is not a generic estimator for arbitrary jump, drift, microstructure-noise or overnight-gap processes. High and low prices must be measured over the same fixed interval and \(H_i,L_i>0\).

The formula's square root, annualized variance, alternative coefficient rounding and equivalent \(1/(4\ln2)\) expression are not separate equations. Parkinson is one range-based volatility-estimator family and is distinct from close-to-close sample variance and GARCH conditional variance, although all estimate or model return variability.

**Disposition:** primary equation and zero-drift assumption verified. Retain as a strong discovery lead, pending token-market scope, sampling interval, price-source and jump/drift contract.

## 2. Bollerslev GARCH(1,1) conditional-variance recursion

### Source and transcription

Tim Bollerslev, *Generalized autoregressive conditional heteroskedasticity*, Journal of Econometrics 31(3) (1986), 307–327, DOI 10.1016/0304-4076(86)90063-1, is the primary source. The paper's general GARCH(p,q) model is commonly transcribed as:
\[
\\sigma_t^2
=\\omega+
\\sum_{i=1}^{p}\\alpha_i\\epsilon_{t-i}^2+
\\sum_{j=1}^{q}\\beta_j\\sigma_{t-j}^2.
\]
The proposed GARCH(1,1) specialization is:
\[
\\sigma_t^2=\\omega+\\alpha\\epsilon_{t-1}^2+\\beta\\sigma_{t-1}^2.
\]
The general equation is the source-level model; GARCH(1,1) is a fixed-order member, not a different model family. The original article metadata and general model are confirmed; the precise GARCH(1,1) notation above is the standard specialization reproduced in later authoritative time-series treatments.

### Parameter and statistical contract

For a positive conditional variance, the standard sufficient conditions include \(\omega>0\), \(\alpha,\beta\geq0\). The covariance-stationary finite-variance condition is \(\alpha+\beta<1\), with unconditional variance \(\omega/(1-\alpha-\beta)\) under the standard innovation assumptions. The innovation process must be defined, e.g. \(\epsilon_t=\sigma_t z_t\) with \(E[z_t]=0\), \(E[z_t^2]=1\). The mean equation for returns is separate from the conditional-variance recursion but is part of the full time-series model.

**Disposition:** primary model lineage and canonical GARCH recursion verified; hold pending return/innovation distribution, mean equation, initialization, stationarity and calibration contract.

## 3. EWMA as an integrated GARCH boundary case

The RiskMetrics EWMA recursion:
\[
\\sigma_t^2=\\lambda\\sigma_{t-1}^2+(1-\\lambda)r_{t-1}^2
\]
is exactly the GARCH(1,1) recursion with \(\omega=0\), \(\alpha=1-\lambda\), and \(\beta=\lambda\). Thus \(\alpha+\beta=1\): it is an IGARCH boundary case with unit persistence and no finite unconditional variance from the standard stationary GARCH formula.

The RiskMetrics 1996 daily \(\lambda=0.94\) is a calibration convention, not a new equation. EWMA and GARCH(1,1) must not be counted as two structurally independent candidates.

## 4. Normal expected shortfall

For a loss variable \(L\\sim\\mathcal N(\\mu,\\sigma^2)\), define the confidence quantile \(z_\\alpha=\\Phi^{-1}(\\alpha)\). The normal VaR is:
\[
VaR_\\alpha=\\mu+\\sigma z_\\alpha.
\]
Expected shortfall is the conditional tail expectation:
\[
ES_\\alpha=E[L\\mid L\\geq VaR_\\alpha].
\]
Using the truncated-normal integral:
\[
ES_\\alpha
=\\mu+\\frac{\\sigma}{1-\\alpha}
\\int_{z_\\alpha}^{\\infty}z\\phi(z)dz
=\\mu+\\sigma\\frac{\\phi(z_\\alpha)}{1-\\alpha}.
\]
This is a derived closed form from the normal distribution and the ES definition; the Basel market-risk framework defines ES as a tail-risk measure but does not make this Gaussian closed form universal.

### Distinction from VaR and scope

ES is a tail mean, whereas VaR is a quantile. The formulas share the same normal distribution parameters and confidence level but are different functionals. Core-15's VaR exclusion does not automatically settle whether normal ES is eligible; the exclusion policy must specify whether it excludes only the VaR quantile or the broader parametric-tail-risk family.

For losses, the tail is \(L\\geq VaR_\\alpha\); for returns, the sign and tail direction change. Freeze the loss convention, horizon, confidence level, mean and volatility estimator. Do not count VaR, ES, conditional tail expectation synonyms or equivalent normal-tail rearrangements as separate independent equations.

**Disposition:** mathematical derivation verified; hold pending an authoritative definition citation, loss/sign convention and the Core-15 VaR-family exclusion ruling.

## 5. Catalogue status and work not performed

The source register now contains 138 records, including RISK-PARKINSON-1980, RISK-BOLLERSLEV-1986 and RISK-RISKMETRICS-1996. No equation-catalogue record was changed: 19 proposed, zero accepted, sampling frame unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls, market-data retrieval or volatility estimation were run. This is source and mathematical review only.
