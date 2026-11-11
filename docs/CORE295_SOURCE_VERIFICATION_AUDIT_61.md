# Core-295 source verification audit 61: Parkinson high–low range volatility estimator

**Date:** 2026-11-11  
**Status:** new peer-reviewed statistical source lead registered as RISK-PARKINSON-1980 (candidate_reference); no equation is added to the formal catalogue or counted toward 295.

## 1. Primary source

Michael Parkinson, “The Extreme Value Method for Estimating the Variance of the Rate of Return,” *The Journal of Business*, 53(1), 61–65 (January 1980), DOI 10.1086/296071. The reviewed author/article PDF reproduces the original derivation and estimator.

The paper models the log price as a one-dimensional continuous random walk with diffusion constant \(D\), equal to the variance of the log-return displacement over a unit time interval. It shows that high and low prices within each interval provide a more efficient estimator of \(D\) than closing prices alone under the assumed process.

## 2. Original extreme-range result

For interval \(i\), define the log high-low range:
\[
\ell_i=\ln\left(\frac{H_i}{L_i}\right).
\]
Under a driftless continuous Brownian/random-walk model, Parkinson derives:
\[
E[\ell_i^2]=4\ln(2)\,D\,\Delta t.
\]
For unit-length intervals:
\[
D=\frac{1}{4\ln 2}E[\ell_i^2]\approx0.36067E[\ell_i^2].
\]
The sample estimator over \(n\) equal-length intervals is:
\[
\widehat{\sigma^2}_{P}
=\frac{1}{4n\ln2}\sum_{i=1}^{n}
\left[\ln\left(\frac{H_i}{L_i}\right)\right]^2
\]
for unit-length intervals. For interval length \(\Delta t\), divide by \(\Delta t\) to obtain variance per unit time.

The original paper also gives the equivalent coefficient \(0.361\) and derives the relation \(E[\ell^2]=1.09(E[\ell])^2\) as a model diagnostic for the assumed random walk.

## 3. Assumptions and limitations

The estimator relies on:
- log prices following a continuous one-dimensional random walk/Brownian motion;
- zero drift over the estimation interval;
- no jumps or discontinuous price gaps;
- high/low observations capturing the continuous intrainterval extremes;
- equal interval length and consistent price units.

It uses only high and low prices. It does not account for opening gaps or explicitly correct for drift, jumps, bid–ask bounce, sparse trading or oracle/AMM microstructure. DeFi pool OHLC data may be distorted by block-time sampling, MEV, oracle updates, pool-specific price impact and thin liquidity. The classical formula should not be applied to such data without a sampling and market-microstructure contract.

## 4. Structural classification

This is a range-based volatility estimator, structurally distinct from:
- close-to-close sample variance;
- realized variance from sums of squared intraperiod returns;
- conditional variance recurrences such as EWMA/GARCH;
- Parkinson's own later range-estimator extensions (e.g. Garman–Klass and Rogers–Satchell), which use additional OHLC fields and must be reviewed as related range-estimator families.

The estimator's scalar constant \(1/(4\ln2)\), sample averaging and annualization are not separate equation candidates. The original expectation identity and its sample estimator are one family.

## 5. Decision

**Disposition:** retain as a strong DeFi Risk statistical-model lead, because it provides a source-backed range estimator that differs structurally from close-to-close and conditional-volatility models. Add Parkinson (1980) to the source register as candidate_reference only. Keep the equation held pending the scalar-form policy, a DeFi-specific OHLC sampling contract and a declared time horizon; do not accept or propose an equation record.

No experiments, volatility estimates, data downloads, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is mathematical source review only.
