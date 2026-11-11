# Core-295 source verification audit 24: Balancer weighted geometric invariant

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed record AMM-BALANCER-WEIGHTED-001 and source AMM-BALANCER-WEIGHTED-MATH.

## 1. Official invariant definition

Balancer's official Weighted Math developer reference defines the pool value/invariant:
[
V=\prod_{i=1}^{n}B_i^{w_i},
qquad
w_i>0,quad \sum_{i=1}^{n}w_i=1,
]
where (B_i) is the normalized balance of token (i) and (w_i) is its normalized weight.

For the proposed three-token adapter:
[
V=B_1^{w_1}B_2^{w_2}B_3^{w_3},
qquad w_1+w_2+w_3=1.
]
This is a fixed-arity adapter to the general (n)-token invariant, not a claim that each token count is a new equation. The invariant is held constant across an idealized swap; fees, token scaling and implementation rounding modify the executable operation.

## 2. Implementation correspondence

The fetched Balancer V2 source file `balancer/balancer-v2-monorepo/pkg/pool-weighted/contracts/WeightedMath.sol` has blob SHA `564887f01a497eb267e22aa22dae6799498ad859`. Its `_calculateInvariant` initializes the fixed-point invariant to one and multiplies, for every token, the balance raised to its normalized weight using downward-rounded fixed-point power and multiplication. It requires the resulting invariant to be positive.

The fetched file content matches the official product-of-weighted-balances invariant. However, the current source-register record does not pin an immutable commit for this file; a moving branch and a file blob SHA are not sufficient for a reproducible implementation pin. The exact commit, pool version and any weighted-pool-specific configuration must be added before source_verified/accepted status.

## 3. Structural and family boundary

The weighted invariant generalizes the constant-product AMM:
- for two tokens with equal weights (w_1=w_2=1/2), (V=sqrt{B_1B_2}), so holding (V) constant is equivalent to (B_1B_2=k), the Core-15 Constant Product exclusion;
- with unequal weights or three or more tokens, the weighted geometric invariant has a different structure from the two-token equal-weight constant-product case;
- the three-token candidate must enforce positive normalized weights summing to one and must not sample them independently.

The spot-price relation and outGivenIn/inGivenOut swap equations are consequences/operations derived from the invariant. They are not extra entries for this candidate. The three-token adapter should be treated as one member of the broader weighted-geometric AMM family, with token-count and weight variations treated as model configuration rather than independent statistical units unless a separate policy justifies otherwise.

## 4. Required benchmark contract

Before acceptance, freeze:
- an immutable Balancer V2 implementation commit and pool version;
- exactly three tokens for this adapter and the permitted normalized-weight domain;
- token order and decimal/upscaling convention;
- positive balances and valid invariant domain;
- swap fee convention and whether the target is the invariant itself or an executable swap;
- fixed-point power/multiplication rounding and invariant ratio limits.

Do not sample arbitrary positive weights and normalize them after the fact without documenting the sampling distribution and its induced dependence. A uniform simplex sample is not the same as independent uniform weights conditioned only by a sum constraint.

## 5. Decision

**Disposition:** official equation and current implementation correspondence verified; retain as a credible DeFi AMM candidate, held pending immutable commit, three-token parameter contract, scaling and rounding adapter. Do not count spot price, swap equations, the two-token equal-weight limit or parameterized pool variants as separate equations.

No catalogue record, source status, proposed count or accepted count was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, live API calls, pool reads or transactions were run. This is documentation and static source review only.
