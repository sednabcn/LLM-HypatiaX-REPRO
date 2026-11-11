# Core-295 source verification audit 9: Carbon adjustable bonding curves and asymmetric orders

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing AMM-CARBON-ADJUSTABLE-CURVES source lead. The primary basis is Carbon whitepaper v1.2 (22 November 2022; last updated 7 January 2023), by Mark Richardson and Stefan Loesch.

## 1. Primary source and exact invariant

The Carbon whitepaper defines the risk-asset-parametrized pool invariant in Eq. (2.1) and Appendix Eq. (A.3):

[
y=P_0x_0rac{x(Gamma-1)-x_0(Gamma-2)}
{Gamma x-x_0(Gamma-1)}.
]

Here (x,y) are risk-asset and numeraire pool state; (P_0) is the reference price; (x_0) is a reference risk-asset volume; and (Gamma) is a dimensionless convexity parameter. The whitepaper focuses on (Gammain[0,1]).

The equivalent swap equation is Eq. (2.6)/(A.9):

[
-Delta y=
rac{P_0Delta x,x_0^2}
{[Gamma(x-x_0)+x_0]
[Gamma(Delta x+x-x_0)+x_0]}.
]

The marginal price is Eq. (2.11)/(A.13):

[
P_{mathrm{marg}}=
rac{P_0x_0^2}{[Gamma(x-x_0)+x_0]^2}.
]

The whitepaper also gives the alternate intercept parameterization (Q=(1-Gamma)^2) and the asymptotic form ((x-x_{mathrm{asym}})(y-y_{mathrm{asym}})=kappa) (Appendix Eq. A.8).

## 2. Structural interpretation: a transformed constant-product family

The primary paper is explicit about the mathematical relationship:
- At (Gamma=1), Eq. (2.5) reduces to (y=P_0x_0^2/x), i.e. (xy=P_0x_0^2), the constant-product curve.
- At (Gamma=0), Eq. (2.4) reduces to (y=P_0(-x+2x_0)), a constant-price straight line.
- For intermediate (Gamma), the whitepaper describes the curve as a translated and scaled constant-product hyperbola.
- The authors state that the curve is financially equivalent to a virtual-token model, with the caveat that the virtual-token parameterization cannot attain the exact constant-price endpoint.

Therefore the adjustable curve's algebraic invariant is not a wholly independent new governing law relative to constant product: it is a parameterized transformation/representation of a hyperbolic constant-product family, with a constant-price limiting case. The fact that the implementation parameterizes the curve through (Gamma,P_0,x_0), or through start/end prices and capacity, does not by itself establish a new structural equation class.

## 3. What is genuinely distinctive: asymmetric order and strategy state

Carbon's separate protocol innovation is that each order trades in one direction only. A strategy can link up to two such orders through shared collateral, allowing a buy curve and a sell curve to have different parameters and independent state. The whitepaper's abstract and Sections 1.3, 3 and conclusion describe:
- one unidirectional curve/order per trading direction;
- independent curve parameters and state;
- up to two linked orders sharing collateral;
- updates to order parameters without withdrawing and recreating liquidity.

These are important market-structure and state-transition properties. They do not turn each direction, order, parameter update, or linked strategy into an independent equation. A protocol-level benchmark could in principle model the complete order/strategy state machine, but that would require a different, explicit domain unit than an equation-only scalar catalogue.

## 4. Catalogue decision

**Current disposition: do not count the adjustable curve as a structurally distinct AMM equation candidate under the current Core-295 structural-distinctness policy.** Retain Carbon as a source-family and protocol-architecture reference, particularly for asymmetric order-state and linked-strategy design.

Reconsider only if the DeFi AMM domain contract is explicitly broadened to include complete executable protocol state machines, with a pinned implementation, a deterministic strategy/order adapter, and a statistical-unit definition. In that case the unit must be the complete linked-order state transition, not one curve equation per order or a new entry for every (Gamma), price range, direction or parameter set.

## 5. Consequences for Core-295

1. Do not use Carbon's family of parameter values as a way to inflate the count with cosmetic formula variants.
2. Do not treat its constant-product endpoint as new relative to the Core-15 constant-product exclusion.
3. Do not label intermediate (Gamma) values statistically independent equations merely because they produce different curve shapes or range settings.
4. Preserve the distinction between an algebraic invariant, a protocol order-state machine, and the strategy composed of linked orders.
5. No formal catalogue entry was accepted or removed by this audit; the source remains in the source register as context.

## 6. Work not performed

No Carbon contracts were executed or queried. No transactions, simulations, experiments, validators, solvers, workflows, paid compute or live API/protocol calls were run. No formal catalogue entry or source status was changed.
