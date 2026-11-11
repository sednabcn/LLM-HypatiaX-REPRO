# Core-295 candidate discovery batch 13: Morpho, Euler and Liquity risk mechanisms

**Status:** protocol and implementation source tracing only. No equation is accepted or counted toward the 59 DeFi Risk target.

## 1. Morpho Blue: LLTV-dependent liquidation incentive factor

**Official documentation:** [Morpho liquidation](https://docs.morpho.org/learn/concepts/liquidation/) and [Collateral, LTV & Health](https://docs.morpho.org/developers/blue/concepts/ltv/). **Implementation:** [Morpho.sol](https://github.com/morpho-org/morpho-blue/blob/main/src/Morpho.sol), captured file blob SHA `ab064b646bf161b1510e2575a99412cdc2a43ebb`; [ConstantsLib.sol](https://github.com/morpho-org/morpho-blue/blob/main/src/libraries/ConstantsLib.sol), blob SHA `1046e6a03462fb68b78dbdcee26339c983dc00de`.

The core contract computes:

\[
LIF=\min\left(M,\frac{1}{1-c(1-LLTV)}\right),
\]

where the current code constants are liquidation cursor \(c=0.3\) and maximum liquidation incentive factor \(M=1.15\). The liquidator repays debt and receives collateral valued at the repayment amount multiplied by this factor, using the market oracle and fixed-point scaling.

**Boundary:** this is a parameterized liquidation-incentive curve indexed by market LLTV, not a liquidation-price equation. It is linked to the LLTV/health-factor family already present in Batch 7. The cap, cursor and fixed-point implementation must be pinned; do not count the displayed percentage bonus, inverse collateral quote and alternative algebraic forms separately.

## 2. Euler EVK: health-dependent reverse-Dutch liquidation discount

**Official documentation:** [Euler liquidations](https://docs.euler.finance/learn/liquidations/) and [EVK whitepaper](https://docs.euler.finance/euler-vault-kit-white-paper/). **Pinned implementation:** [Liquidation.sol](https://github.com/euler-xyz/euler-vault-kit/blob/93a1de491531e54cbbcf0e5c8cacfe558f924867/src/EVault/modules/Liquidation.sol), file blob SHA `8ce05719f1200e543b1b81ad5c749780e4cf7df4`.

The implementation calculates the risk-adjusted collateral-to-liability health ratio:

\[
h=\frac{C_{adj}}{L},
\]

then defines the collateral discount factor as:

\[
d_f=\max\left(h,1-D_{max}\right),
\qquad
D=1-d_f,
\]

where \(D_{max}\) is the vault-configured maximum liquidation discount. The liquidator's maximum collateral value relative to debt value is scaled by \(1/d_f\). The discount therefore starts at zero at the liquidation boundary, increases as health deteriorates, and is capped by the vault configuration.

**Boundary:** the current implementation expresses the reverse-Dutch discount as a function of health shortfall, not elapsed auction time. Keep the health ratio, discount factor and collateral quote within one Euler liquidation family. Risk-adjusted collateral aggregation, oracle conversion, rounding, maximum discount and cool-off checks are implementation conditions, not independent equations. The formula is version-specific; preserve the pinned source commit.

## 3. Liquity V1: Stability Pool debt offset and collateral redistribution

**Official documentation:** [Stability Pool and Liquidations](https://docs.liquity.org/liquity-v1/faq/stability-pool-and-liquidations) and [Recovery Mode](https://docs.liquity.org/liquity-v1/faq/recovery-mode).

In normal liquidation, the Stability Pool burns LUSD equal to the liquidated Trove's remaining debt and receives its collateral, less the liquidation initiator's gas compensation. The pool's depositors share the debt loss and collateral gain pro rata to their deposits. In Recovery Mode, the liquidation branch depends on individual collateral ratio, minimum collateral ratio, total collateral ratio and available Stability Pool deposits. For an under-MCR position with insufficient Stability Pool liquidity, the offset portion of collateral is proportional to the fraction of debt offset; remaining debt/collateral is redistributed to active Troves.

**Boundary:** this is a stateful loss-absorption and redistribution mechanism, not simply another LTV/health-factor ratio. The full Stability Pool accounting uses product/sum accumulators and epoch/scale transitions; a scalar pro-rata expression is only a high-level summary. Do not count the liquidation threshold, gas compensation, offset fraction and collateral gain as independent equations without a formal state-transition model and exact whitepaper/contract mapping.

## Cross-protocol overlap controls

- Morpho LIF and Euler's health-dependent discount are distinct liquidation-incentive mechanisms, but both belong to the liquidation-incentive source cluster. Protocol-specific implementations are not automatically independent statistical units.
- Aave HF, Morpho LTV/LLTV and Euler risk-adjusted collateral health all compare collateral capacity with debt/liability. They are related risk-ratio families; avoid counting each protocol's naming convention as a separate structural equation.
- Liquity Stability Pool is a different risk-sharing mechanism: it absorbs debt and receives collateral, with pro-rata depositor accounting and Recovery Mode state transitions.
- The Core-15 liquidation-price exclusion remains active. Do not introduce liquidation price through a rearranged LTV or collateral-ratio expression.
- Fixed-point scales, WAD conversions, oracle-price scaling, rounding direction, and configured parameter values are implementation details, not new equations.

## Acceptance requirements

Pin the exact contract commit, protocol version, constants, market/vault parameters, oracle quote units, fixed-point scales, rounding, liquidation eligibility conditions, debt/collateral accounting and state transitions. Any Stability Pool candidate requires a complete accumulator/epoch/scale derivation rather than a simplified pro-rata description. All sources remain candidates.

No experiment, live protocol call or workflow has been run.
