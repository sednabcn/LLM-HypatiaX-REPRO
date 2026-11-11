# Core-295 source verification audit 53: BIS DeFi wallet leverage and collateral-implied leverage

**Date:** 2026-11-11  
**Status:** classification of existing source-register lead RISK-BIS-LEVERAGE; no equation is added to the formal catalogue or counted toward 295.

## 1. Primary source and empirical scope

Lioba Heimbach and Wenqian Huang, *DeFi Leverage*, BIS Working Papers No. 1171, Bank for International Settlements, March 2024.

The paper uses wallet-day data from Aave V1, Aave V2 and Compound V2, covering 1 January 2021 to 31 March 2023. It defines wallet leverage as asset value divided by equity and compares this with the maximum leverage implied by protocol loan-to-value (LTV) limits. It also studies associations between leverage, borrowing costs, market movements, near-liquidation exposure and collateral substitution.

## 2. Leverage definitions

Let \(A_w\) be the total USD value of wallet assets included in the authors' balance-sheet measure, \(D_w\) the corresponding debt value, and \(E_w=A_w-D_w\) equity. Actual wallet leverage is:
\[
L_w=\frac{A_w}{E_w}=\frac{A_w}{A_w-D_w}.
\]
For a single collateral asset with maximum LTV ratio \(\ell\), the maximum debt is \(\ell A\), leaving equity \((1-\ell)A\). The corresponding LTV-implied leverage is:
\[
L_{\max}=\frac{1}{1-\ell}.
\]
These are standard balance-sheet leverage and collateral-haircut identities, not new DeFi-specific constitutive equations. In multi-asset portfolios, the actual wallet metric depends on the paper's aggregation and asset-coverage rules; it is not simply the inverse of one LTV parameter.

The paper also labels its resilience outcome “VaR” as the share of loans close to liquidation, and separately measures liquidation share. This is not conventional portfolio Value-at-Risk in the quantile-loss sense. Do not confuse the paper's operational label with standard VaR.

## 3. Empirical model and unit-of-analysis limitations

The study uses wallet-day panel observations and protocol-level market/risk variables. Its results are empirical associations about leverage and lending resilience, not a universal law mapping leverage to liquidation probability. The paper reports that higher leverage is associated with a larger share of loans close to liquidation, but not a statistically significant increase in realized liquidation incidence; liquidation is described as event-driven and costly.

The wallet is a pseudo-anonymous address-level unit, not necessarily a beneficial owner or economic entity. The paper explicitly notes that one wallet may represent multiple investors and one investor may use multiple wallets. The wallet-level leverage observation therefore does not establish independent borrower units.

A source transcription check also identifies a numerical inconsistency to preserve for any future replication: the text on PDF page 8 states 11,130,928 observations for 55,948 users, while Table 3's Total row reports 13,094,094 observations and 57,555 wallets. The platform-specific Table 3 counts sum to 16,846,950 observations and 63,588 wallets. These figures should be reconciled against the authors' data/code before any sample-size or replication claim is made.

## 4. Structural classification

The paper is valuable empirical context for portfolio-level leverage and lending resilience. Its leverage ratios are standard accounting definitions; its regression specifications and risk-share measures are sample-dependent estimators. None is a new protocol equation suitable for the 295 structural equation target.

Do not count actual leverage, LTV-implied leverage, collateral haircut, near-liquidation share, liquidation share, or the panel regression variants as independent equation candidates. The wallet-level data aggregation also does not create independent statistical units where multiple addresses may belong to the same economic participant.

## 5. Decision

**Disposition:** retain RISK-BIS-LEVERAGE as empirical DeFi portfolio-risk context, not as a new structural equation candidate. Preserve the paper's distinction between actual asset-to-equity leverage and LTV-implied maximum leverage. Flag the sample-count inconsistency and wallet-ownership ambiguity for any future replication or independence analysis.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No data downloads, regressions, wallet clustering, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is paper-level source review only.
