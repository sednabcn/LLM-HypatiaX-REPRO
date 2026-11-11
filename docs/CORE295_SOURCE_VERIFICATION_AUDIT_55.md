# Core-295 source verification audit 55: Under-collateralized DeFi leverage and liquidation-constrained maximum multiplier

**Date:** 2026-11-11  
**Status:** new primary research lead identified; source-register addition proposed below. No equation is added to the formal catalogue or counted toward 295.

## 1. Primary source

Zhipeng Wang, Kaihua Qin, Duc Vu Minh and Arthur Gervais, “Speculative Multipliers on DeFi: Quantifying On-Chain Leverage Risks,” *Financial Cryptography and Data Security (FC 2022)*, pp. 38–56, DOI 10.1007/978-3-031-18283-9_3. Open author-accepted manuscript: UCL Discovery, eprint 10182322, file 71.pdf.

The paper formalizes under-collateralized on-chain leverage, using Alpha Homora as its empirical case study. It models three borrower risks: AMM impermanent loss, arbitrage loss and collateral liquidation.

## 2. Formal position and leverage model

For one collateral token \(C\), one borrowed token \(B\), collateral amount \(Coll_t\), borrowed amount \(Borr_t\), exchange rate \(p_t^{B\to C}\), and platform credit parameter \(Credit(B,C)\), the paper defines:
\[
DebtRatio_t=
\frac{Borr_t}{Coll_t}\,
Credit(B,C)\,p_t^{B\to C}.
\]
The position becomes liquidatable when \(DebtRatio_t>1\).

Its leverage multiplier is:
\[
LM_t=
\frac{Borr_t\,p_t^{B\to C}+Coll_t}{Coll_t}.
\]
This is a single-collateral, single-debt asset/equity-style leverage measure. It is not the same as the LTV-implied leverage definition in BIS Working Paper 1171 (Audit 53), and the two should not be silently conflated.

## 3. AMM return and arbitrage components

The paper assumes a generic AMM conservation function \(f(x_t,y_t,\bar k)=0\), with marginal price given by the ratio of partial derivatives. Its constant-product specialization \(x_ty_t=k\), spot price \(y_t/x_t\), and reserve-swap equation are standard CP relations and overlap the existing AMM/impermanent-loss families.

For a CP pool, it derives the familiar divergence-loss expression:
\[
Loss^{IL}_{cp}=
\frac{2\sqrt{p/p_0}}{1+p/p_0}-1.
\]
This is not a new independent candidate under the Core-15 Impermanent Loss exclusion.

The paper also derives arbitrage loss when a borrower's liquidity-supply swap moves one CP pool's price away from an unchanged second pool:
\[
Loss^{AR}=
\delta y_2\left(\frac{p_t^{B\to C}}{p_{t+\delta}^{B\to C}}-1\right).
\]
The CP specialization is proportional to the borrower's supplied trade size and the arbitrageur's counter-trade size. This is a scenario-specific two-pool arbitrage relation, not a new invariant; it depends on the two-pool price gap and ignores fees/latency in the stylized derivation.

## 4. Liquidation threshold and loss

For initial leverage multiplier \(m\), the paper derives the liquidation threshold condition:
\[
\frac{\widehat p_l^{B\to C}}{p_{t_0}^{B\to C}}
\leq
\frac{1}{Credit(B,C)(m-1)}
\]
for the boundary of the safe region under its price convention. The corresponding liquidation loss, normalized by initial collateral, is:
\[
Loss^{LQ}=
(m-1)\,LS\,c_l\,
\frac{p_t^{B\to C}}{p_{t_0}^{B\to C}},
\]
where \(LS\in(0,1]\) is the liquidation spread and \(c_l\in(0,1]\) is the fraction of debt repaid by the liquidator.

## 5. Maximum reasonable leverage result

The paper combines two constraints:
1. The position must not be liquidatable immediately after opening, including the assumed worst-case price movement.
2. The liquidation reward must remain sufficiently attractive to liquidators, represented by \(Loss^{LQ}\leq1\) in the paper's normalization.

Taking the worst-case liquidator repayment fraction \(c_l=1\), and defining the maximum price ratio over the risk horizon as:
\[
q_{\max}=\max_t\frac{p_t^{B\to C}}{p_{t_0}^{B\to C}},
\]
the paper obtains:
\[
m_{\max}=
1+\frac{1}{\max(LS,Credit(B,C))\,q_{\max}}.
\]
This is the most distinctive scalar result in the paper. It couples the platform credit setting, liquidation spread and bounded adverse price movement into a maximum leverage constraint.

It is not a universal leverage law: it assumes one collateral/debt pair, a fixed credit parameter, a fixed liquidation spread, a specified price-ratio bound, and the paper's simplified liquidation-loss and incentive conditions. The \(q_{\max}\) horizon and direction of the exchange-rate convention must be frozen explicitly.

## 6. Structural classification and source-family decision

The paper's CP invariant, spot price, CP impermanent-loss equation and generic health/liquidation ratio overlap existing AMM and lending-risk families. Its maximum-reasonable-leverage bound is a distinct constrained-risk result, but it is derived from the same leverage/liquidation system and must be treated as one family with the threshold and liquidation-loss equations.

Do not count separately:
- debt ratio and liquidation eligibility;
- leverage multiplier;
- liquidation threshold price;
- liquidation loss;
- maximum leverage bound;
- CP impermanent loss and CP arbitrage specializations.

The empirical Alpha Homora observations and the paper's 9-month dataset do not create independent equation units. The paper is a peer-reviewed conference contribution, but the model is an analytical abstraction rather than a current protocol implementation specification.

## 7. Adapter and validity requirements

A deterministic adapter must freeze:
- one collateral token and one borrowed token, or a separately specified multi-asset extension;
- token units and the orientation of \(p^{B\to C}\);
- \(Credit(B,C)\), \(LS\), initial collateral/debt and leverage \(m\);
- the price-risk horizon and the definition of \(q_{\max}\);
- the liquidator repayment fraction and the \(Loss^{LQ}\leq1\) incentive condition;
- whether AMM IL/arbitrage components are excluded because of Core-15 overlap;
- no fees, interest, oracle latency, slippage, or additional state transitions unless explicitly added to the model.

## 8. Decision

**Disposition:** retain as a strong DeFi Risk analytical candidate lead, particularly the liquidation-constrained maximum leverage relation. Add the peer-reviewed source to the source register as candidate_reference only. Keep all equations held pending the structural-equivalence rule, a bounded price-horizon definition and a deterministic one-pair adapter. Do not add an accepted or proposed equation record.

No experiments, on-chain data extraction, solver runs, validators, workflows, paid compute, API calls, or protocol transactions were run. This is mathematical source review only.
