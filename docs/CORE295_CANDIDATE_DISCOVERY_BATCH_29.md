# Core-295 candidate discovery batch 29: Balancer V2 Linear Pool invariant

**Date:** 2026-11-11  
**Status:** discovery-only source lead. Not added to the formal catalogue or counted toward 295.  
**Domain focus:** DeFi AMM.

## 1. Source and invariant

**Official documentation:** Balancer V2 Linear Math and Linear Pools documentation.  
**Implementation inspected:** `balancer/balancer-v2-monorepo/pkg/pool-linear/contracts/LinearMath.sol`, fetched file blob SHA `54b0ced4b671cb87fb8efac301553c2eaca48572`.

Balancer's code comments state that a Linear Pool holds a main token, a wrapped/yield-bearing counterpart and BPT. The wrapped token has a trusted exchange rate into main-token units. The pool's invariant is the sum of the nominal main balance and the rate-normalized wrapped balance:
[
I=N(B_m;L,U,f)+R B_w,
]
where (B_m) is the real main-token balance, (B_w) the wrapped-token balance, (R) the wrapped-to-main exchange rate, (L,U) the lower/upper target balances and (f) the fee parameter. In the implementation, the wrapped balance is already upscaled by the wrapped-token rate before entering `_calcInvariant`, and:
[
\_calcInvariant(N_m,B_w^{(m)})=N_m+B_w^{(m)}.
]

The nominal main balance is piecewise affine:
[
N(B_m;L,U,f)=
\begin{cases}
B_m-f(L-B_m),&B_m<L,\\
B_m,&L\leq B_m\leq U,\\
B_m-f(B_m-U),&B_m>U.
\end{cases}
]
This is exactly the implementation's `_toNominal` operation: fees are assessed on the amount by which the main balance lies outside the target interval. The invariant is held constant across swaps after applying this nominal-balance transform.

## 2. Protocol architecture and model boundary

The pool is designed for a main token and a wrapped/yield-bearing counterpart with a known exchange rate (e.g. DAI/aDAI). It has lower and upper target balances for the main token:
- swaps that move the main balance farther outside the target range pay a proportional fee;
- swaps that move it back toward the target range receive an incentive funded from fees;
- the wrapped token is valued in main-token units using a trusted rate provider;
- BPT is backed by nominal reserves and is preminted; its virtual supply determines the pool-share conversion.

The BPT supply conversion, `_fromNominal` inverse, the 12 directional/given-in/given-out swap functions, and the rebalancer are operations on the same invariant and target-fee state. They are not separate independent equation candidates.

## 3. Structural family comparison

The invariant is constant-sum after the piecewise nominal-balance and rate transformations. It is distinct from:
- constant product (xy=k), including virtual-reserve translations;
- weighted geometric invariant (prod_i B_i^{w_i});
- finite-amplification Curve StableSwap/CryptoSwap invariants;
- DODO's inventory-dependent PMM curve;
- Gyro E-CLP's ellipse.

It is related to the constant-sum/high-amplification limit of stable-swap AMMs and to other linear pools. Do not count separate candidates for different target intervals, wrapped-token rates, token decimal conventions, fee levels or swap directions.

The exact piecewise nominal transform makes this more than an unmodified two-token (x+y=k) relation, but the underlying invariant remains linear sum. The structural-equivalence policy should decide whether the nominal transform is part of the equation identity or a protocol-specific fee adapter around a constant-sum invariant.

## 4. Main blockers

- The source register currently lacks an immutable Balancer V2 commit for the inspected `LinearMath.sol` blob; the branch/file SHA is not a reproducible version pin.
- Freeze exact pool/factory implementation, rate-provider semantics, token decimals/upscaling, target ranges, fee scale, and fixed-point rounding.
- Define whether the target equation is the constant-sum invariant (I=N_m+B_w^{(m)}), the piecewise nominal transform (N(B_m)), or the full state transition. They are not three independent equations.
- Constrain the wrapped-token rate to a valid positive range and model its temporal evolution only if it is part of the declared input/state contract.
- Define whether protocol-specific constant-sum pools are within the DeFi AMM domain and whether this family is distinct from the limiting constant-sum form of amplified stable-swap.

## 5. Initial disposition

**Disposition:** credible additional DeFi AMM source lead. Keep discovery-only pending immutable implementation pin, precise target/fee/rate adapter and a constant-sum-versus-stable-swap structural ruling. Do not add an equation record or count parameterized pool variants.

## 6. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, pool reads or transactions were run. This is documentation and static source discovery only.
