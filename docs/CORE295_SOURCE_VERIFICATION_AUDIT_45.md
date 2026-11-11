# Core-295 source verification audit 45: Morpho Blue liquidation incentive factor

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead RISK-MORPHO-LIF; no equation is added to the formal catalogue or counted toward 295.

## 1. Official formula

Morpho's liquidation documentation defines the liquidation incentive factor (LIF) as a function of the market's liquidation loan-to-value threshold (LLTV):
\[
LIF=\min\left(M,\frac{1}{\beta\,LLTV+(1-\beta)}\right),
\]
with documented default parameters \(\beta=0.3\) and \(M=1.15\). Algebraically:
\[
LIF=\min\left(M,\frac{1}{1-\beta(1-LLTV)}\right).
\]
The newer Morpho Midnight documentation describes the same expression using a liquidation cursor \(\gamma\):
\[
maxLif=\frac{1}{1-\gamma(1-LLTV)}.
\]
The parameter naming changed, but the functional form is the same when \(\gamma=\beta\); the maximum cap is applied in the implementation.

## 2. Pinned Morpho Blue implementation

Repository: morpho-org/morpho-blue  
Commit: 430bd61d8ab9238c1bde327eec2bfcd3f494fe9d  
File: src/Morpho.sol  
Blob SHA: ab064b646bf161b1510e2575a99412cdc2a43ebb

The liquidation function computes:
\[
LIF=\min\left(LIF_{\max},
\frac{1}{1-\text{LIQUIDATION\_CURSOR}(1-LLTV)}\right)
\]
using WAD fixed-point multiplication/division and downward rounding for the factor. The pinned source comment states the same formula. It then:
- converts collateral value to loan-token units using the oracle price and ORACLE_PRICE_SCALE;
- applies the LIF to determine the collateral seized for a given debt repayment, or inversely determines repayment for a specified seized collateral amount;
- uses directional rounding (up/down) for shares, assets and collateral;
- handles residual bad debt if collateral is exhausted.

Thus LIF is one parameterized incentive function within a larger liquidation state transition. The collateral-seizure conversion and debt-share arithmetic are operations using LIF, not separate incentive equations.

## 3. Structural classification

The LIF formula is a capped reciprocal of an affine function of LLTV. It is distinct from:
- Aave's weighted collateral-threshold health factor;
- Morpho's own LTV/health-factor ratio;
- Compound/Aave piecewise-linear utilization-based borrow-rate curves;
- liquidation-price equations and generic liquidation bonus parameters.

It is related to the liquidation threshold and collateral-seizure process, but should be treated as one Morpho liquidation-incentive family. Different LLTV values, cursor values, maximum caps and market deployments do not create independent equation candidates.

The Morpho Blue and Morpho Midnight docs should not be silently conflated if their implementation versions or liquidation paths differ. This audit pins the current Morpho Blue source commit and records the shared functional form.

## 4. Acceptance adapter and scope

A deterministic adapter must freeze:
- Morpho Blue implementation/version and exact market parameters;
- LLTV, liquidation cursor and maximum LIF cap;
- oracle price scale and collateral/loan token decimal conventions;
- whether the input is debt repaid or collateral seized;
- WAD fixed-point arithmetic and rounding directions;
- health eligibility, partial liquidation and bad-debt handling if the full liquidation transition is modeled.

The LIF formula alone is a scalar protocol parameter rule; the full liquidation operation is a system-level state transition. The benchmark must declare which is the unit.

## 5. Decision

**Disposition:** official formula and pinned implementation verified. Retain as a credible DeFi Risk lead, held pending the protocol-risk domain rule and a deterministic parameter/rounding adapter. Do not count LIF, collateral-seizure conversion, health factor and liquidation state transition as separate independent equations.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, on-chain reads or liquidation transactions were run. This is documentation and static-source review only.
