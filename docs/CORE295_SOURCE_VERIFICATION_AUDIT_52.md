# Core-295 source verification audit 52: Miqado reversible-call-option liquidation mitigation

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead RISK-IACR-LIQUIDATIONS; no equation is added to the formal catalogue or counted toward 295.

## 1. Primary research source and scope

Kaihua Qin, Jens Ernstberger, Liyi Zhou, Philipp Jovanovic and Arthur Gervais, *Mitigating Decentralized Finance Liquidations with Reversible Call Options*, IACR ePrint 2023/254; arXiv:2303.15162v2 (28 March 2023). The paper introduces Miqado, a lending-position support mechanism using a reversible European call option.

The paper's base position is a single debt asset and a single collateral asset, \(P_t=\langle D_t,C_t\rangle\), with oracle exchange rate \(p_t\). It explicitly notes that real lending pools can contain multiple collateral and debt assets; the paper's mathematical model is a single-asset abstraction.

## 2. Baseline health and fixed-spread model

The paper defines:
\[
HF_t(P)=\frac{C_t p_t\theta}{D_t},
\qquad
CR_t(P)=\frac{C_t p_t}{D_t},
\]
where \(0<\theta<1\) is the configured collateral discount. A position is unhealthy when \(HF_t(P)<1\).

Its fixed-spread baseline uses close factor \(k_{CF}\) and liquidation spread \(S\). The maximum collateral claim is:
\[
Q=(D_t k_{CF})(1+S),
\]
and the idealized liquidator profit is:
\[
\Pi=(D_t k_{CF})S.
\]
These are baseline FSL definitions and overlap the generic fixed-spread family reviewed in Audit 51; they are not Miqado's novel contribution.

## 3. Reversible call-option primitive

The reversible call option is parameterized by asset \(A\), amount \(N\), strike \(K\), reimbursement factor \(k\) and maturity \(T\). The buyer pays premium \(\phi\) at initialization. Before maturity, the seller may terminate the option by reimbursing the buyer \(k\phi\), with \(k>1\). If not terminated, the buyer can exercise at maturity.

The paper gives the buyer's maturity payoff in its scalar notation:
\[
P_{CB}=
\begin{cases}
A(T)-K-\phi,&A(T)\ge K,\\
-\phi,&A(T)<K.
\end{cases}
\]
The pre-maturity reimbursement is a separate contract outcome, not an ordinary European call payoff. The paper's primitive is therefore a European call augmented with an issuer/seller termination right and a premium reimbursement.

## 4. Miqado lending-position transitions

A supporter may enter at \(t_0\) when:
\[
HF_{t_0}(P)<1.
\]
The supporter adds \(\lambda C_{t_0}\) of collateral to the lending position and receives the reversible option/right to take over the position at maturity \(T\). The premium factor \(\lambda\) is a protocol parameter.

Before maturity, the borrower may rescue/terminate the support arrangement by repaying:
\[
C_{re}=\lambda C_{t_0}(1+I_L)k_{re},
\]
where \(I_L\) is the borrower's agreed loan interest rate and \(0<k_{re}<1\) is an implementation-dependent risk factor.

At maturity, the supporter either takes over the position or defaults according to the option's exercise economics. If the protocol coexists with conventional liquidation, the paper introduces a buffer-based support eligibility factor:
\[
k_{SF}=CR_{t_0}(P)(\theta+B)<1,
\]
with buffer parameter \(B>1\). This gives supporters an eligibility region before ordinary liquidation eligibility is reached.

## 5. Option premium model and limitation

The paper uses Black–Scholes to estimate the reversible option premium factor:
\[
\lambda^*=
\frac{p_{t_0}e^{-r_fT}N(d_1)-Ke^{-I_LT}N(d_2)}
{C_{t_0}p_{t_0}},
\]
with:
\[
d_1=\frac{\ln(p_{t_0}/K)+(I_L-r_f+\sigma^2/2)T}
{\sigma\sqrt{T}},
\qquad
d_2=d_1-\sigma\sqrt{T}.
\]
Here \(r_f\) is the foreign interest rate, \(I_L\) the protocol borrowing rate, and \(\sigma\) the underlying-price volatility. The paper explicitly cautions that this Black–Scholes approximation does not account for the reduction in risk/average payoff caused by the seller's early termination right; a more precise reversible-option pricing model is left for future work. Thus \(\lambda^*\) is a proposed proxy under Black–Scholes assumptions, not an exact fair-value formula for the reversible option.

## 6. Structural classification

Miqado is a complete debt-support and liquidation-mitigation mechanism, not merely a variant of a health factor or liquidation bonus. Its distinct structure couples:
- an unhealthy-position trigger;
- third-party collateral top-up;
- a reversible call option;
- seller-initiated early termination at a reimbursement premium;
- borrower rescue payment;
- maturity takeover/default;
- optional buffer eligibility relative to conventional liquidation.

Do not count the baseline health factor, fixed-spread liquidation claim, option payoff, early repayment, support eligibility, Black–Scholes proxy and maturity outcomes as independent equations. They are components of one Miqado system. The option payoff and ordinary call option share a family, but the seller's pre-maturity termination right changes the contract state machine.

## 7. Adapter and acceptance requirements

A deterministic adapter must freeze:
- paper version and single-collateral/single-debt abstraction;
- \(p_t,\theta,\lambda,k_{CF},S,I_L,k_{re},K,T,\sigma,r_f\);
- support entry time and eligibility;
- amount and unit of top-up collateral;
- early termination timing and reimbursement factor;
- maturity exercise/default rule and ownership/transfer of debt/collateral;
- whether conventional liquidation remains available and exact buffer \(B\);
- option valuation convention, including explicit acknowledgment that the paper's Black–Scholes proxy omits early-termination value.

## 8. Decision

**Disposition:** retain Miqado as a strong DeFi Risk complete-system candidate lead. Its reversible-call-option support and early-termination state transition are structurally distinct from the reviewed health-factor, fixed-spread liquidation, Dutch-auction, Morpho LIF and Euler health-shortfall discount families. Hold pending the system-unit policy and a fully specified deterministic adapter. Do not count the linked scalar equations and option pricing components separately.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, blockchain replays, simulations, pricing calculations, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is paper-level mathematical source review only.
