# Core-295 source verification audit 50: OECD empirical liquidation–DEX volatility model

**Date:** 2026-11-11  
**Status:** classification of existing source-register lead RISK-OECD-LIQUIDATIONS; no equation is added to the formal catalogue or counted toward 295.

## 1. Source and empirical scope

Ana Sasi-Brodesky and Iota Kaousar Nassr, *DeFi liquidations: Volatility and liquidity*, OECD Working Papers on Finance, Insurance and Private Pensions No. 48 (2023), DOI 10.1787/0524faaf-en.

The study uses transaction-level data for Aave V1/V2, Compound and Maker from 1 December 2020 to 8 December 2022. Its main empirical sample focuses on USDC debt collateralized by ETH/WETH, with liquidations aggregated across the included Aave and Compound pools. Maker is not in that pair-specific sample because the studied Maker system only lent DAI.

The paper studies whether liquidation activity is associated with subsequent DEX price volatility. It does not specify a protocol-independent liquidation mechanism or a structural lending-risk law.

## 2. Realized-volatility measure

The paper constructs one-minute continuously compounded returns:
\[
r_{t+k}=\ln P_{t+k}-\ln P_{t+k-1}.
\]
For the baseline two-hour window, realized volatility is:
\[
Vol_{t+1}=
\sqrt{\sum_{k=0}^{119}r_{t+k}^{\,2}}.
\]
The estimate uses 120 one-minute return observations and assumes zero-mean returns for this realized-variance measure. A separate robustness specification uses 30 one-minute observations for a 30-minute horizon.

This is a standard realized-volatility construction, not a new DeFi-specific structural equation. Its window length and return sampling interval are design choices.

## 3. OLS empirical specification

The baseline model is:
\[
\log(Vol_{t+1})=
\beta_0+\beta_1\log(LIQ_t)+\beta_2\log(Vol_t)
+\beta_3R_t+\beta_4I_t+\beta_5(R_tI_t)+\epsilon_{t+1}.
\]
Here:
- \(LIQ_t\) is the USD value (millions) of USDC debt liquidated in the prior two-hour interval;
- \(Vol_t\) is realized volatility over the preceding two-hour interval;
- \(R_t\) is the previous two-hour USDC/WETH price return;
- \(I_t=1\) when \(R_t>0\), otherwise zero.

The study applies logarithms to volatility and liquidation amounts and discards zero-liquidation observations. It reports a positive association between liquidated debt and subsequent realized volatility in the sample.

The paper also estimates a 2SLS specification using the adjustable USDC borrowing rate as an instrument for liquidations. The second-stage outcome is same-window realized volatility; this is an empirical identification strategy, not a general risk-state equation.

## 4. Structural and benchmark classification

The study contributes empirical evidence about liquidation clustering, DEX liquidity dependence and post-liquidation volatility. It is relevant context for the DeFi Risk domain, but the equations are:
- a conventional realized-volatility estimator;
- a sample-specific log-linear econometric regression;
- an instrumental-variable estimation design.

They are not independent protocol equations, and the paper's coefficient estimates are not transferable parameters for a synthetic equation catalogue. The empirical relation also depends on a specific token pair, protocols, observation window, transaction dataset, filtering of zero liquidations and chosen two-hour/30-minute horizons.

Do not count the realized-volatility definition, OLS model, 2SLS first/second stages, lagged-volatility terms or alternative window lengths as independent equation candidates.

## 5. Decision

**Disposition:** retain RISK-OECD-LIQUIDATIONS as empirical context and a potential motivation for a separate systemic-liquidation-risk study. Do not count it as a new protocol-independent DeFi Risk equation. If the benchmark later includes empirical econometric models, it requires a separately defined task family and reproducible dataset/provenance contract; the 2020–2022 sample and estimated coefficients must not be presented as universal protocol laws.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, regressions, data downloads, validators, workflows, paid compute, API calls, on-chain reads or transactions were run. This is paper-level source review only.
