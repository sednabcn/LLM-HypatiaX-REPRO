# Core-295 source verification audit 46: Euler EVK health-shortfall liquidation discount

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead RISK-EULER-REVERSE-AUCTION; no equation is added to the formal catalogue or counted toward 295.

## 1. Official liquidation mechanism

Euler's liquidation documentation describes a reverse Dutch auction:
- discount is zero at the liquidation threshold;
- discount increases linearly as account health worsens;
- discount is capped by the vault's configured maximum liquidation discount;
- the liquidator inherits selected debt and receives discounted collateral in the same operation.

The health measure is:
\[
h=\frac{C_{\mathrm{adj}}}{L},
\]
where \(C_{\mathrm{adj}}\) is risk-adjusted collateral value and \(L\) is liability value. Liquidation is eligible when \(h<1\).

## 2. Pinned implementation and exact discount equation

Repository: euler-xyz/euler-vault-kit  
Commit: 93a1de491531e54cbbcf0e5c8cacfe558f924867 (29 October 2026)  
File: src/EVault/modules/Liquidation.sol  
Blob SHA: 8ce05719f1200e543b1b81ad5c749780e4cf7df4

The calculateLiquidation logic computes:
\[
h=\frac{C_{\mathrm{adj}}}{L}
\]
using risk-adjusted collateral and liability values. It then computes a discount factor:
\[
f_d=\max\left(h,1-d_{\max}\right),
\]
where \(d_{\max}\) is the configured maximum discount (scaled by CONFIG_SCALE). Therefore the liquidation discount is:
\[
d(h)=1-f_d
=\min\left(1-h,d_{\max}\right),
\qquad 0\leq h<1.
\]
At the liquidation threshold \(h=1\), the discount is zero; as health worsens, the discount rises linearly until it reaches \(d_{\max}\).

The implementation then computes maximum collateral yield value using \(L/f_d\), limits the yield to the borrower's available collateral, and reduces the repay amount if necessary. Oracle mid-point prices, collateral and debt balances, rounding and vault configuration affect the actual assets transferred.

## 3. Structural comparison

Euler's capped linear health-shortfall discount differs from Morpho Blue's capped reciprocal incentive factor:
\[
LIF_{\mathrm{Morpho}}=
\min\left(LIF_{\max},
\frac{1}{1-\gamma(1-LLTV)}\right).
\]
Euler's discount is a piecewise-linear function of the current health ratio; Morpho's LIF is a reciprocal function of market LLTV and liquidation cursor. These are different functional structures, although both are liquidation-incentive rules and share the broader liquidation-risk family.

The reverse-auction terminology should not be interpreted as a time-decaying auction: the discount depends on health shortfall, not elapsed time. The health ratio, discount factor, discount, collateral-yield conversion and max-repay computation are parts of one liquidation transition, not independent equation candidates.

## 4. Adapter and version requirements

A deterministic adapter must freeze:
- exact Euler Vault Kit version and commit;
- risk-adjusted collateral valuation and liability valuation;
- maximum liquidation discount and CONFIG_SCALE;
- collateral/debt oracle and mid-point price convention;
- collateral selection, repay cap, available collateral and debt takeover semantics;
- fixed-point precision, rounding and health checks after position transfer;
- optional cool-off time and socialization conditions if the complete liquidation system is modeled.

## 5. Decision

**Disposition:** official mechanism and exact capped-linear health-shortfall discount verified against a pinned EVK implementation. Retain as a credible DeFi Risk candidate lead, distinct in functional form from Morpho's LIF. Hold pending a deterministic health/discount/settlement adapter and a decision on whether the benchmark counts protocol-specific liquidation incentive rules as equation units.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, on-chain reads or liquidation transactions were run. This is documentation and static-source review only.
