# Core-295 source verification audit 8: DODO Proactive Market Maker (PMM)

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing AMM-DODO-PMM-MATH source lead. The review checks the official PMM derivation against the exact implementation commit already registered in the source catalogue.

## 1. Source and version identity

The source register identifies the official DODO “The Math Behind” documentation and pins the implementation repository DODOEX/contractV2 at commit `2f1bcdac7ef1beee7599a756e2eed26732c2536d`, specifically:
- `contracts/lib/PMMPricing.sol`, fetched blob SHA `257332467f7973b74f2ebae441a894c93d54a579`;
- `contracts/lib/DODOMath.sol`, fetched blob SHA `8e4e6a1254afeab8bfe70ee552a1ebde2117423a`.

The implementation uses Solidity 0.6.9, fixed-point decimal arithmetic, explicit floor/ceiling operations, and a piecewise inventory state. This is an implementation-specific PMM snapshot, not a claim that all DODO pool types or later deployments share identical parameters and execution behavior.

## 2. Marginal price curve

The official mathematical derivation defines marginal price as (P=iR), with guide/reference price (i), slippage factor (k), current base inventory (B), current quote inventory (Q), and equilibrium/target inventories (B_0,Q_0). The curve is piecewise:

[
P(B,Q)=
egin{cases}
ileft(1-k+kleft(rac{B_0}{B}ight)^2ight), & B<B_0,\[4pt]
displaystylerac{i}{1-k+kleft(rac{Q_0}{Q}ight)^2}, & Q<Q_0,\[8pt]
i, & 	ext{otherwise.}
end{cases}
]

The first branch represents a shortage of base inventory and a marginal price above the guide price. The second represents a shortage of quote inventory and a marginal price below the guide price. The equilibrium branch is the guide price. The PMM state also records whether the price state (R) is ONE, ABOVE_ONE or BELOW_ONE.

The marginal price curve is not itself the average execution price for a finite trade. The latter is obtained by integrating marginal price along the inventory path.

## 3. Integrated trade equation and quadratic inversion

For the base-shortage branch, the official derivation gives the quote amount required to move base inventory from (B_1) to (B_2):

[
Delta Q
=i(B_2-B_1)left(1-k+krac{B_0^2}{B_1B_2}ight).
]

Thus the average execution price is

[
ar P=rac{Delta Q}{B_2-B_1}
=ileft(1-k+krac{B_0^2}{B_1B_2}ight).
]

If (Delta Q), (B_0), (B_1), (i) and (k) are given, the new inventory (B_2) is obtained from a quadratic equation. The positive root is selected under the documented nonnegative-inventory condition. The quote-shortage branch is symmetric after exchanging base/quote inventories and using reciprocal guide price.

The pinned `DODOMath._GeneralIntegrate` implements the integral in fixed-point arithmetic and explicitly documents its ordering constraint (V_0geq V_1geq V_2>0), supports the endpoint cases (k=0) and (k=1), and rounds down. `_SolveQuadraticFunctionForTrade` handles the quadratic inversion, special-cases (k=0) and (k=1), uses a ceiling operation for the solved inventory root, and returns the reserve delta. `PMMPricing.sol` routes trades through different routines according to the current R-state and changes state when a trade crosses the equilibrium inventory.

## 4. State transitions are part of the model

The implementation does more than evaluate a static price function. It:
- tracks (B,Q,B_0,Q_0,i,k) and the discrete R-state;
- calculates trades on the correct branch;
- detects whether the trade remains in the current branch, reaches equilibrium, or crosses to the opposite branch;
- updates the R-state and uses the relevant target-adjustment calculation;
- applies fixed-point scaling, overflow-safe arithmetic and explicit rounding.

The whitepaper-style marginal curve, the integrated trade amount, the quadratic inversion, the equilibrium-target adjustment and the R-state transition are not separate independent equation candidates. They are mathematical components of one piecewise PMM inventory/state-transition model.

## 5. Structural-family assessment

DODO PMM is a credible DeFi AMM family distinct in form from:
- constant-product reserve invariant (xy=k);
- Balancer's weighted-product invariant;
- Liquidity Book's discrete constant-sum bins;
- Uniswap v3's continuous concentrated-liquidity position model.

Its distinctive structure is a guide-price-centered, piecewise inventory-dependent marginal price with a quadratic inventory-ratio penalty and integrated finite-trade execution. It is a strong candidate lead, but a family-level distinction does not establish statistical independence from other AMM equations or from other parameterizations of the same PMM.

## 6. Required before catalogue promotion

1. Freeze the exact implementation commit and identify which DODO pool implementation/version the benchmark represents; do not generalize from this library to every DODO pool type.
2. Define the model unit as the complete piecewise price/inventory state transition, not one formula per branch, trade direction or helper.
3. Specify units and token orientation for (i,B,Q,B_0,Q_0), and the normalization convention for fixed-point decimal values.
4. Constrain (0leq kleq1), positive inventories and all branch-specific target/order relations; specify the valid state transitions and trade-size limits.
5. Preserve implementation rounding and special cases if claiming contract-level reproduction; otherwise label the benchmark as the ideal real-valued mathematical model and keep it distinct from the Solidity execution model.
6. Define the deterministic input/state generator and the independent statistical unit. Multiple swaps from one pool state trajectory must not be treated as independent equations.

## 7. Decision

**Current disposition: strong equation-family lead; held, not accepted.** The official derivation and pinned implementation agree on the PMM's piecewise inventory-dependent price and integrated trade mechanics. Promotion remains blocked on a frozen model contract, unit/range contract, and independence policy. No formal catalogue count changes.

## 8. Work not performed

No contracts were executed or deployed. No transactions, simulations, experiments, solvers, validators, workflows, paid compute or live API/protocol calls were run. No formal catalogue entry or source status was changed.
