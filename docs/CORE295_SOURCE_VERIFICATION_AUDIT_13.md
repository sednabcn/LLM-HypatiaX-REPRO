# Core-295 source verification audit 13: Euler EVK health-dependent liquidation discount

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing source-register lead `RISK-EULER-REVERSE-AUCTION`. Official Euler liquidation documentation and the exact pinned EVK `Liquidation.sol` source were checked. This audit also compares the mechanism with the already-screened Morpho LIF. No on-chain query or protocol call was made.

## 1. Official mechanism and source pin

The source register pins `euler-xyz/euler-vault-kit` commit `93a1de491531e54cbbcf0e5c8cacfe558f924867`, file `src/EVault/modules/Liquidation.sol`, blob SHA `8ce05719f1200e543b1b81ad5c749780e4cf7df4`.

Euler's official documentation describes a reverse-Dutch-style liquidation discount: the discount is zero at the liquidation threshold, grows linearly as health deteriorates, and is capped by a vault-configured maximum. The liquidator takes over selected debt and receives collateral in the same operation; this is not a conventional auction whose discount is a function of elapsed auction time.

## 2. Exact equation transcription

Let (C_{mathrm{risk}}) be the risk-adjusted collateral value and (D) the liability value, both measured in the same unit of account. The position health is
[
h=rac{C_{mathrm{risk}}}{D}.
]
A position is eligible for liquidation when (hleq1), subject to the exact raw on-chain comparisons and zero-liability case.

Let (min[0,1]) be the configured maximum liquidation discount. The pinned implementation computes the discount factor:
[
f=max(h,1-m).
]
Equivalently, the collateral discount is
[
d=1-f=min(1-h,m).
]
For a repay value (R), the corresponding maximum collateral yield value is
[
Y_{max}=rac{R}{f},
]
before collateral availability limits, oracle conversion, asset rounding and other execution constraints.

The code implements the lower bound on (f) using the configured maximum discount scaled by `CONFIG_SCALE`; it calculates health from the risk-adjusted collateral/liability values using fixed-point arithmetic. The output called `discountFactor` is the retained factor (f), not the discount (d). Confusing these two quantities reverses the economic interpretation.

## 3. Full model and implementation boundaries

The scalar expression is only the incentive component of the liquidation operation. The protocol:
- computes risk-adjusted collateral using liquidation LTVs and oracle quotes in a common unit of account;
- calculates liability value;
- applies the health-dependent discount factor and maximum-discount floor;
- converts debt and collateral using oracle prices;
- limits the collateral yield to the violator's available collateral and adjusts repay when collateral is insufficient;
- transfers debt and collateral positions under the vault/EVC checks.

These operations are parts of one liquidation state transition, not separate independent equation candidates. The benchmark must freeze the selected collateral/liability assets, risk-adjusted LTVs, oracle/unit-of-account configuration, (m), price convention, available collateral, fixed-point scale, rounding and implementation commit.

The current EVK documentation notes that displayed health may be rounded; benchmark inputs must use exact numerical health, not UI display values.

## 4. Comparison with Morpho Blue LIF

Morpho's already-verified liquidation incentive factor is
[
mathrm{LIF}=minleft(1.15,rac{1}{1-0.3(1-mathrm{LLTV})}ight),
]
a capped rational function of a market-level liquidation threshold parameter.

Euler's function instead depends on the individual position's current health (h) and the vault's maximum discount (m):
[
f=max(h,1-m).
]
The mechanisms therefore differ in their input state and functional structure:
- Morpho: market LLTV (ightarrow) capped rational incentive factor;
- Euler: position health (ightarrow) linearly increasing discount, capped by vault configuration.

They are structurally distinct candidate equations within the broader liquidation-incentive source family. Their shared DeFi liquidation context does not prove independent statistical units. Both must remain in one source-family cluster for sampling design and dependence review.

## 5. Decision

**Disposition:** the Euler health-dependent capped discount is source- and implementation-verified and is a credible structurally distinct DeFi Risk candidate. Keep it held pending a frozen adapter for risk-adjusted collateral valuation, unit of account, maximum discount, oracle/rounding and the complete selected-asset liquidation contract. Do not count the health ratio, discount complement, collateral yield conversion or repay/yield branches as additional equations.

No catalogue record or status was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

## 6. Work not performed

No experiment, solver, validator, workflow, paid compute, live API call, oracle query, on-chain read or transaction was run. This is source and static implementation review only.
