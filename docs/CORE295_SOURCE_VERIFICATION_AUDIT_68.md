# Core-295 source verification audit 68: Rogers–Satchell drift-independent range volatility estimator

**Date:** 2026-11-11  
**Status:** verification of a related but structurally distinct statistical-risk source lead. No equation is added to the formal catalogue or counted toward 295.

## 1. Primary source

L. C. G. Rogers and S. E. Satchell, “Estimating Variance from High, Low and Closing Prices,” *The Annals of Applied Probability*, 1(4), 504–512 (1991), DOI: 10.1214/aoap/1177005835.

The primary article's abstract models log price as Brownian motion with drift, \(\sigma B_t+ct\), and proposes a variance estimator based on high, low and closing prices that is unbiased for arbitrary drift. The authors also discuss discretely observed extrema and a correction for the error from approximating continuous extrema with transaction-time/random-walk extrema.

Primary-source locations:
- Institute of Mathematical Statistics / Project Euclid: https://projecteuclid.org/download/pdf/euclid.aoap/1177005835
- Author publication copy: https://www.skokholm.co.uk/wp-content/uploads/2016/01/R_Satchell_HLOC.pdf

## 2. Estimator transcription

Use the prior closing price as the base price for the next observation interval. Define:
\[
H_t=\ln\left(\frac{High_t}{Close_{t-1}}\right),\quad
L_t=\ln\left(\frac{Low_t}{Close_{t-1}}\right),\quad
C_t=\ln\left(\frac{Close_t}{Close_{t-1}}\right).
\]
The one-interval Rogers–Satchell contribution is:
\[
q_{RS,t}=H_t(H_t-C_t)+L_t(L_t-C_t).
\]
For \(n\) equal-length intervals, the sample variance estimator is:
\[
\widehat{\sigma^2}_{RS}
=\frac{1}{n}\sum_{t=1}^{n}
\left[H_t(H_t-C_t)+L_t(L_t-C_t)\right].
\]
The paper's central property is drift-unbiasedness under the continuous Brownian log-price model. This is not the Parkinson estimator: the latter uses only squared high–low log range and assumes zero drift, while Rogers–Satchell uses the high, low and terminal close relative to the interval's starting reference and remains unbiased for arbitrary constant drift under its model.

The notation above is normalized for the benchmark description. Preserve the original paper's observation convention and its treatment of the unobserved continuous extrema when drafting a formal record; do not silently equate transaction-time extrema with continuous-path extrema.

## 3. Assumptions and limitations

The source model assumes:
- log price follows a continuous Brownian motion with constant volatility and drift over the interval;
- interval increments are modeled consistently and intervals have known/equal duration for the simple average;
- high, low and closing observations refer to the same interval and price process;
- no unmodeled jumps, market closures, stale observations or discontinuous oracle updates;
- observed highs/lows approximate the continuous extrema, with the paper's discrete-observation correction relevant when that approximation is material.

For DeFi use, a sampling contract must define venue/pool, token direction, reserve or oracle price, block/time boundaries, treatment of zero-trade intervals, price impact, MEV, liquidity changes, decimal normalization and whether highs/lows are continuous-time or sampled extrema. The classical estimator is not automatically valid for block-sampled pool OHLC data.

## 4. Structural-family assessment

Provisional family: **RISK-RANGE-VOLATILITY**.

- Parkinson (1980) is a high–low-only estimator with a zero-drift Brownian assumption.
- Rogers–Satchell (1991) uses high, low and close relative to the interval start and removes the constant-drift restriction in its continuous Brownian model.
- Garman–Klass and Yang–Zhang are related OHLC range-estimator methods and require their own source and assumption reviews.

The Rogers–Satchell functional is not an algebraic rearrangement of Parkinson's squared range estimator. Nevertheless, the estimators share OHLC observations, Brownian path assumptions and a common range-volatility source family. They must not be treated as independent statistical samples merely because their formulae differ. Annualization, averaging, log-price normalization and alternate notation are not separate equation candidates.

## 5. Decision

**Disposition:** retain Rogers–Satchell (1991) as a source-verified candidate_reference lead in the same broad range-volatility family as Parkinson, with a distinct drift treatment and OHLC functional. Hold it from proposed/accepted equation counts pending:
1. explicit policy on whether distinct statistical estimators within one source family qualify as separate equation units;
2. exact transcription of the paper's discrete-extrema correction and the intended observation convention;
3. a DeFi OHLC sampling and market-microstructure contract;
4. a statistical dependence plan that does not treat Parkinson and Rogers–Satchell estimates from the same price path as independent observations.

No formal equation-catalogue record was added or accepted. No source-register count is changed by this audit. The formal catalogue remains at 19 proposed records and zero accepted equations; the sampling frame remains unfrozen.

No experiments, volatility estimates, data downloads, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is primary-source mathematical review only.
