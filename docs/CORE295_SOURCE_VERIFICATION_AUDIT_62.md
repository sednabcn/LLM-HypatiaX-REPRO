# Core-295 source verification audit 62: Merton structural corporate-credit model

**Date:** 2026-11-11  
**Status:** new peer-reviewed primary research lead registered as RISK-MERTON-1974 (candidate_reference); no equation is added to the formal catalogue or counted toward 295.

## 1. Primary source

Robert C. Merton, “On the Pricing of Corporate Debt: The Risk Structure of Interest Rates,” *The Journal of Finance*, 29(2), 449–470 (May 1974), DOI 10.1111/j.1540-6261.1974.tb03058.x.

The paper models firm value as a continuous diffusion and shows that levered equity is equivalent to a European call option on firm assets, with the face value of debt as strike. Risky debt is the residual firm value less equity.

## 2. Firm-value process and terminal claims

In the zero-payout, single homogeneous debt class specialization, firm asset value follows geometric Brownian motion:
\[
\frac{dV_t}{V_t}=\mu\,dt+\sigma_V\,dW_t.
\]
At maturity \(T\), with promised debt face value \(B\):
\[
E_T=\max(V_T-B,0),
\qquad
D_T=\min(V_T,B).
\]
Equity holders default when \(V_T<B\); debt holders take over the firm in the model's bankruptcy boundary condition.

## 3. Closed-form option/debt values

Under the risk-neutral pricing measure, with constant risk-free rate \(r\), zero payouts and volatility \(\sigma_V\):
\[
d_1=\frac{\ln(V_0/B)+(r+\tfrac12\sigma_V^2)T}
{\sigma_V\sqrt{T}},
\qquad
d_2=d_1-\sigma_V\sqrt{T}.
\]
Equity is:
\[
E_0=V_0\Phi(d_1)-Be^{-rT}\Phi(d_2).
\]
Risky debt is:
\[
D_0=V_0-E_0
=V_0\Phi(-d_1)+Be^{-rT}\Phi(d_2).
\]
The risk-neutral probability of default is:
\[
Q(V_T<B)=\Phi(-d_2).
\]
The paper's more general framework includes firm payouts and derives a parabolic pricing PDE with corresponding boundary conditions; the closed-form option specialization above requires the stated zero-payout/constant-parameter assumptions.

## 4. Distance-to-default distinction

A physical-measure distance-to-default statistic commonly replaces the risk-neutral drift \(r\) in \(d_2\) with the physical expected asset drift \(\mu\):
\[
DD=
\frac{\ln(V_0/B)+(\mu-\tfrac12\sigma_V^2)T}
{\sigma_V\sqrt{T}}.
\]
Then \(\Phi(-DD)\) is a physical-measure default probability under the GBM assumptions. This is not the same probability as the risk-neutral \(\Phi(-d_2)\) from the debt-pricing formula. The original paper's option-pricing \(d_2\) must not be relabeled as a physical default probability without specifying the measure and drift.

## 5. Structural classification and DeFi mapping

The Merton model is a structural credit-risk model, distinct from:
- weighted collateral health factors (Aave/Euler);
- fixed-spread liquidation optimization (Qin et al.);
- liquidation incentive/auction mechanisms (Morpho, Euler, Maker);
- volatility estimators such as Parkinson, EWMA and GARCH.

It is not a direct model of an on-chain lending position. A DeFi adapter would need to define what constitutes firm/protocol asset value \(V\), senior debt barrier \(B\), maturity \(T\), asset volatility and payout/fee process. For a borrower-level collateral position, liquidation is generally a path-dependent threshold event with partial repayment and collateral seizure, not the single terminal default barrier assumed by the basic Merton model.

## 6. Decision

**Disposition:** retain as a strong DeFi Risk structural-credit-model lead, particularly for protocol/DAO treasury solvency or a clearly defined pooled balance sheet. Add Merton (1974) to the source register as candidate_reference only. Hold the formula pending a defensible DeFi balance-sheet mapping and explicit physical-versus-risk-neutral probability convention. Do not count equity option value, risky debt value, \(d_1\), \(d_2\), default probability and distance-to-default as separate equations.

No experiments, calibrations, simulations, data downloads, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is primary-paper mathematical review only.
