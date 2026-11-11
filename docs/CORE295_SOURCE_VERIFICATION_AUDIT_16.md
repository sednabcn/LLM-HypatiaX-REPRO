# Core-295 source verification audit 16: Aave V3 multi-collateral health factor and liquidation-health family

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing source-register lead RISK-AAVE-HEALTH. Aave V3 official documentation was compared with the already-screened Morpho Blue and Euler EVK health definitions. No on-chain position or oracle was queried.

## 1. Aave V3 official definition

Aave's official V3 documentation defines health factor as total collateral value multiplied by the weighted-average collateral liquidation threshold, divided by total borrow value:
[
mathrm{HF}_{Aave}
=rac{C_{mathrm{tot}}overline{LT}}{D_{mathrm{tot}}}.
]
For collateral assets (i), with value (C_i) in a common unit and liquidation threshold (LT_i),
[
overline{LT}
=rac{sum_i C_i LT_i}{sum_i C_i}.
]
Therefore the expanded form is
[
mathrm{HF}_{Aave}
=rac{sum_i C_i LT_i}{D_{mathrm{tot}}}.
]
A position with health factor below 1 is eligible for liquidation under the documented threshold rule.

The formula is portfolio-level: the numerator aggregates collateral values after applying each collateral asset's liquidation threshold; the denominator aggregates debt values in the same reference unit. It is not the arithmetic average of thresholds without collateral-value weights.

## 2. Comparison with Morpho and Euler

The already-verified source records define:
- Morpho Blue: (mathrm{HF}_{Morpho}=Ccdot Pcdotmathrm{LLTV}/D) for the market's collateral/debt pair;
- Euler EVK: (h_{Euler}=C_{mathrm{risk}}/D), where risk-adjusted collateral is the sum of collateral values weighted by their liquidation LTVs.

Aave's expanded multi-collateral expression has the same general mathematical form as Euler's risk-adjusted collateral ratio. Morpho's single-collateral market formula is the one-collateral special case of the same weighted collateral/debt structure. The differences are in portfolio aggregation, threshold semantics, market architecture and protocol implementation—not a new independent health-factor family.

Accordingly:
- retain Aave as a source for the multi-collateral weighted-threshold adapter and portfolio-level assumptions;
- do not count Aave HF, Morpho HF and Euler health as three structurally independent equations under the current equation-only policy;
- do not count the weighted-average threshold identity as a separate equation from the expanded weighted-sum health factor;
- keep health factor separate from liquidation incentive functions: Aave/Morpho/Euler health determines eligibility or risk state, while Morpho LIF and Euler's capped discount determine collateral incentive/transfer amounts.

## 3. Benchmark contract implications

Aave's adapter would need to freeze:
- collateral and debt asset sets and common unit of account;
- price oracle conventions and token decimals;
- per-asset liquidation thresholds and eligible collateral flags;
- treatment of accrued debt and collateral balances;
- portfolio aggregation and fixed-point rounding;
- the exact Aave V3 release/market configuration.

A single-collateral scalar example is not representative of the multi-collateral formula. Conversely, generating arbitrary independent thresholds and balances without portfolio constraints would not reflect a valid protocol position.

## 4. Decision

**Disposition:** source verified; retain as multi-collateral implementation/context evidence for the shared collateral-health family, not as an additional structurally distinct candidate alongside Morpho/Euler health. No new proposed record is justified by this source alone.

No catalogue record or status was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, live API calls, oracle queries, on-chain reads or protocol transactions were run. This is documentation-level source review only.
