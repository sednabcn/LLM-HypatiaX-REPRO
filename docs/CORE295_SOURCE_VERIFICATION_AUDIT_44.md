# Core-295 source verification audit 44: Aave V3 health factor and Compound III kinked borrow-rate model

**Date:** 2026-11-11  
**Status:** verification of existing DeFi Risk source leads; no equation is added to the formal catalogue or counted toward 295.

## 1. Aave V3 health factor

### Official definition

Aave V3 documentation defines:
\[
HF=\frac{\text{Total Collateral Value}\times
\text{Weighted Average Liquidation Threshold}}
{\text{Total Borrow Value}}.
\]
The weighted average liquidation threshold is collateral-value weighted. If \(C_i\) is the eligible collateral value in the oracle base currency and \(LT_i\) its liquidation threshold:
\[
\overline{LT}=
\frac{\sum_i C_i LT_i}{\sum_i C_i},
\qquad
HF=\frac{\sum_i C_i LT_i}{\sum_j D_j},
\]
where \(D_j\) are debt values in the same base currency. A position is eligible for liquidation when \(HF<1\).

### Pinned V3 implementation

Repository: aave/aave-v3-core  
Commit: 782f51917056a53a2c228701058a6c3fb233684a  
File: contracts/protocol/libraries/logic/GenericLogic.sol  
Blob SHA: 3342316e772a7e733723ef2963ab79566904fb30

The pinned calculateUserAccountData implementation:
- iterates over reserves the user uses as collateral or debt;
- reads each asset's oracle price and decimals;
- includes collateral only when its liquidation threshold is nonzero and the user has enabled it as collateral;
- accumulates collateral value weighted by each asset's liquidation threshold;
- accumulates debt value from stable and variable debt balances, with normalized variable debt;
- applies eMode-specific thresholds and oracle prices where applicable;
- divides the weighted sum by total collateral to obtain the average liquidation threshold;
- calculates health factor as collateral value multiplied by average liquidation threshold, divided by total debt.

The implementation returns an effectively infinite health factor when total debt is zero. The deployed implementation uses percentage/ray/wad fixed-point arithmetic and rounding, not unrestricted real arithmetic.

### Structural boundary

Health factor is a collateralization-risk metric and liquidation-eligibility ratio. It is not a liquidation price: for multiple collateral and debt assets, Aave explicitly notes that liquidation price is a curve of price combinations rather than one scalar price. The threshold \(HF<1\) is an eligibility predicate attached to the metric, not a separate equation candidate.

A deterministic adapter must freeze the collateral set, debt set, oracle base currency/prices, asset decimals, collateral flags, liquidation thresholds, eMode category, stable/variable debt balances, accrued interest and fixed-point rounding. The aggregate formula is one Aave health-factor family; don't count the weighted-average threshold, each reserve contribution and the liquidation predicate separately.

**Disposition:** official definition and pinned V3 code path verified. Retain as a credible DeFi Risk scalar metric lead, discovery-only, pending cross-protocol structural comparison and a coherent multi-asset sampling contract.

## 2. Compound III utilization-based borrow-rate model

### Official rate function

Compound III documentation defines utilization:
\[
U=\frac{\text{Total Borrows}}{\text{Total Supply}}.
\]
The borrow rate is a per-second rate, scaled by \(10^{18}\), with a utilization kink \(U_k\):
\[
r_b(U)=
\begin{cases}
r_0+s_L U,&U\leq U_k,\\
r_0+s_L U_k+s_H(U-U_k),&U>U_k.
\end{cases}
\]
Here \(r_0\) is the base per-second borrow rate, \(s_L\) and \(s_H\) are low/high slopes, and \(U_k\) is the borrow kink. Compound's documentation says interest accrues every second using block timestamps. APR is approximated by multiplying the per-second rate by seconds per year; that conversion is not a separate equation.

### Structural comparison

Aave V3's variable borrow-rate model also uses a two-slope piecewise-linear function with an optimal utilization point. Differences in parameter scaling, utilization normalization, reserve factors, per-second vs annualized units and parameter names do not create independent structures. Group Compound and Aave kinked borrow-rate functions into one piecewise-linear utilization-rate family unless a later protocol has a materially different functional form or state structure.

The supply-rate function is related but includes utilization and reserve-factor effects; it should be treated as a separate derived rate output only if the catalogue's unit explicitly distinguishes borrow and supply pricing functions. It is not another independent sample merely because it uses separate parameters.

**Disposition:** Compound III piecewise-linear borrow-rate equation and utilization definition verified against official docs. Retain as one DeFi Risk rate-model family lead, pending the cross-protocol piecewise-linear family rule and an exact parameter/rate-unit adapter.

## 3. Cross-protocol and independence conclusion

Aave health factor and Compound utilization-kink borrow rate are different structures:
- health factor is a weighted collateral/debt ratio used for liquidation eligibility;
- borrow rate is a piecewise-linear constitutive function of utilization.

Aave V3's own two-slope rate curve is structurally related to Compound III's curve and should be grouped with it. Different protocol parameter values or names do not create independent equation units. Health factor, weighted liquidation threshold and liquidation-price boundaries are related outputs of one collateralization-risk family.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, on-chain reads or transactions were run. This is official-documentation and static-source review only.
