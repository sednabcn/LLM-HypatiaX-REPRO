# Core-295 source verification audit 17: Compound III collateral storefront discount

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing source-register lead RISK-COMPOUND-LIQUIDATION. Official Compound III liquidation/governance documentation and the pinned Comet implementation already recorded for the Compound III rate source were checked. No market was queried and no protocol call was made.

## 1. Protocol role and official definition

Compound III separates liquidation eligibility from collateral sale:
- liquidation eligibility is determined by liquidation collateral factors, which are distinct from borrow collateral factors;
- an eligible account is absorbed by the protocol, transferring its collateral to Comet and its debt to the protocol balance sheet;
- if protocol base-asset reserves are below the governance-set target, third parties can buy seized collateral at a discount using the base asset.

The storefront discount is not the liquidation eligibility threshold, and it is not the incentive paid to the account that calls absorb. It is a price reduction applied when selling collateral already held by the protocol.

## 2. Exact discount and quote equations

The official documentation defines:
[
d_{mathrm{store}}
=mathrm{StoreFrontPriceFactor},(1-mathrm{LiquidationFactor}_{a}),
]
where the liquidation factor is asset-specific and both parameters are WAD-scaled protocol factors.

The discounted collateral price is
[
P_{a,mathrm{discounted}}
=P_a(1-d_{mathrm{store}}).
]
For a base-asset payment (B), the amount of collateral quoted is, in normalized economic units,
[
A_a
=rac{P_b B}{P_{a,mathrm{discounted}}}
]
with the implementation applying the asset and base-token decimal scales:
[
A_a
=rac{P_b,B,mathrm{assetScale}}
{P_{a,mathrm{discounted}},mathrm{baseScale}}.
]

The source register's pinned implementation is `compound-finance/comet` commit `f766f51583c23acc33b2a7824654ef2029a96804`, `contracts/CometWithExtendedAssetList.sol`, blob SHA `3490e984d133789aa1afe2e8f7e37a11d2512396`. Its `quoteCollateral` implementation follows the formula above: computes the discount from the storefront factor and asset liquidation factor, discounts the collateral feed price, reads the base-token price, and applies the asset/base scales.

## 3. Structural and family comparison

This is a configured proportional price discount, not a dynamic health-dependent auction:
- unlike Euler EVK, the discount does not increase with the current position health shortfall;
- unlike Morpho Blue, it is not a capped rational function of LLTV;
- unlike Sky Abacus, it is not a function of elapsed auction time;
- unlike Aave/Morpho/Euler health factors, it does not determine liquidation eligibility.

It is also not a standalone liquidation process. It is one price quote inside Compound's post-absorption collateral-sale process. The protocol's absorption logic, reserve target, governance parameters, collateral oracle and base-token oracle determine when and how the quote is used.

The discount equation is a short affine product and is not by itself a strong structurally rich equation candidate. Its value is as a source-specific member of the broader liquidation-price/incentive family. The amount-out quote is a dimensional conversion built on that discount, not an additional independent equation.

## 4. Decision

**Disposition:** source and pinned implementation verified; retain as protocol-specific liquidation-sale pricing context, not as an additional structurally distinct candidate at this stage. Do not count the discount-factor identity, discounted price, decimal conversion or reserve-target condition as separate equations. Revisit only if the predeclared catalogue policy includes configured post-absorption collateral sale rules as a distinct equation family and specifies a deterministic quote adapter.

No catalogue record or status was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

## 5. Work not performed

No experiments, solvers, validators, workflows, paid compute, live API calls, oracle queries, on-chain reads or protocol transactions were run. This is documentation and static source review only.
