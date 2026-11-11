# Core-295 source verification audit 49: Compound III collateral liquidation factors and reserve absorption

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead RISK-COMPOUND-LIQUIDATION; no equation is added to the formal catalogue or counted toward 295.

## 1. Pinned implementation

Repository: compound-finance/comet  
Commit: f766f51583c23acc33b2a7824654ef2029a96804  
File: contracts/CometWithExtendedAssetList.sol  
Blob SHA: 3490e984d133789aa1afe2e8f7e37a11d2512396

This is the Comet implementation variant with extended asset-list support. Do not assume that every deployed Comet market uses this exact source revision or asset-list extension.

## 2. Liquidation eligibility

The isLiquidatable implementation starts with the account's present-value base principal. A nonnegative principal is not liquidatable. For a borrower, it values the debt in the base token's oracle price and adds each enabled collateral's oracle value multiplied by its configured liquidateCollateralFactor:
\[
L_{\mathrm{adj}}=
-P_B^{mid}B^{debt}
+\sum_i P_i^{mid}q_i\,LF_i^{liq}.
\]
The account is liquidatable when:
\[
L_{\mathrm{adj}}<0.
\]
The code exits early if the running adjusted liquidity becomes nonnegative. Price scaling and asset-specific scales are applied in integer arithmetic.

## 3. Reserve absorption and collateral factors

The absorbInternal path first requires the account to be liquidatable. It seizes all enabled collateral balances, values each collateral at its oracle price, and multiplies each value by the separate liquidationFactor:
\[
V_{\mathrm{absorb}}=
\sum_i P_i^{mid}q_i\,LF_i^{absorb}.
\]
It converts that amount to base-token units and adds it to the borrower's negative base balance. If the result remains negative, it is clamped to zero: the excess debt is absorbed by protocol reserves. The account's collateral flags are reset, and total supply/borrow accounting is updated to reflect reserve-funded debt repayment.

The code distinguishes liquidateCollateralFactor (used for liquidation eligibility) from liquidationFactor (used in reserve absorption and storefront discount calculations). They must not be silently treated as one parameter.

## 4. Storefront collateral quote

The buyCollateral quote computes a discount from the liquidationFactor and storeFrontPriceFactor:
\[
d_i=SF\,(1-LF_i^{absorb}),
\qquad
P_i^{disc}=P_i^{mid}(1-d_i).
\]
The quoted collateral amount for base amount \(B\) is:
\[
q_i^{out}=
\frac{P_B^{mid}\,B\,scale_i}
{P_i^{disc}\,baseScale}.
\]
The implementation then checks the buyer's minimum output, collateral reserves and the protocol's base-reserve target before transferring collateral. This storefront discount is not the same as the account's liquidation eligibility threshold.

## 5. Structural classification

Compound III combines:
- a multi-collateral liquidation eligibility inequality;
- protocol-reserve absorption of seized collateral and bad debt;
- a separate liquidation-factor valuation;
- a reserve-conditioned collateral storefront discount and quote.

The eligibility inequality is in the broad collateral-weighted health/liquidation family with Aave and Euler; variable names and per-asset parameters do not by themselves establish structural independence. The reserve absorption and storefront quote are protocol-specific state/settlement mechanics, not extra independent scalar health equations.

Do not count the eligibility check, reserve absorption valuation, discount factor, discounted price, collateral quote and reserve updates separately. Treat the full absorb-and-buy lifecycle as one Compound III liquidation/reserve-management system if complete protocol systems are allowed by the eventual policy.

## 6. Adapter requirements

Freeze:
- exact Comet deployment and implementation variant;
- base token, collateral list, token scales and oracle prices;
- present-value debt and accrued-interest indices;
- liquidateCollateralFactor and liquidationFactor separately for every asset;
- storeFrontPriceFactor and targetReserves;
- collateral balances, enabled asset flags and protocol reserve state;
- fixed-point factor/price arithmetic and integer rounding;
- absorb ordering, residual debt clamp and buyCollateral reserve/output checks.

## 7. Decision

**Disposition:** pinned implementation confirms a multi-asset liquidation eligibility inequality, reserve-funded debt absorption and a distinct storefront discount/quote function. Retain as a DeFi Risk system lead, held pending the exact deployment adapter and comparison with the already reviewed Aave/Euler health-factor family. The complete reserve-absorption mechanism may be system-distinct; do not count its component formulas separately.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, on-chain reads or transactions were run. This is static-source review only.
