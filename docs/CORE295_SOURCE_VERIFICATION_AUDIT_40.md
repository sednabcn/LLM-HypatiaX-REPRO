# Core-295 source verification audit 40: Balancer V2 Linear Pool invariant and nominal-balance fee transform

**Date:** 2026-11-11  
**Status:** verification of discovery-batch 29 lead only. No equation is added to the formal catalogue or counted toward 295.

## 1. Pinned implementation

Repository: balancer/balancer-v2-monorepo  
Commit: e91a2b643a49856f51a648d175667c1b48cf3377  
Files:
- pkg/pool-linear/contracts/LinearMath.sol, blob SHA 54b0ced4b671cb87fb8efac301553c2eaca48572
- pkg/pool-linear/contracts/LinearPool.sol, fetched at the same commit.

The implementation's _calcInvariant is exactly:
\[
I=N_m+B_w^{(m)},
\]
where \(N_m\) is the nominal main-token balance and \(B_w^{(m)}\) is the wrapped-token balance already upscaled into main-token units by the pool's scaling factors. The LinearPool getRate path fetches vault balances, upscales them using the pool's scaling factors, applies _toNominal to the main balance, then calls _calcInvariant and divides by virtual BPT supply.

The nominal main-balance transform is implemented as:
\[
N_m(B_m)=
\begin{cases}
B_m-f(L-B_m),&B_m<L,\\
B_m,&L\leq B_m\leq U,\\
B_m-f(B_m-U),&B_m>U,
\end{cases}
\]
where \(L\) and \(U\) are lower and upper targets and \(f\) is the swap-fee percentage. The source rounds the fee down consistently. The inverse _fromNominal uses the corresponding piecewise algebraic inverse and directed fixed-point rounding.

## 2. Protocol interpretation

The pool combines:
- a main token;
- a wrapped/yield-bearing token, valued in main-token units by a rate provider;
- BPT representing the pool share.

The linear invariant is the sum of nominal main balance and rate-normalized wrapped balance. Outside the target interval, the nominal main balance is reduced by a fee proportional to the distance from the nearest target. Inside the target interval, nominal and real main balances coincide.

The invariant itself is constant sum after applying the nominal transform and wrapped-token scaling. The BPT conversion and _fromNominal inverse are derived operations; swap directions and joins/exits are state-transition wrappers, not separate equations.

## 3. Structural classification and relationship to StableSwap

This is an exact linear-sum invariant with a piecewise fee transform. It is not the finite-amplification StableSwap polynomial, not the dynamic-\(K\) CryptoSwap invariant, not a positive-weight geometric invariant, and not DODO's inventory-dependent PMM.

The constant-sum relation is related to the high-amplification/near-peg limit of StableSwap, but the Linear Pool's rate-normalized main/wrapped-token structure and piecewise target fee transform define a separate protocol mechanism. Whether that is a separate structural equation unit depends on the declared scalar-form vs complete-protocol rule.

Do not count:
- the untransformed sum, nominal balance transform and inverse transform separately;
- BPT rate, join/exit, exact-in/exact-out swap and fee calculations;
- different lower/upper targets, rate-provider values, fee levels or token decimals.

## 4. Decision

**Disposition:** pinned implementation and exact piecewise nominal-sum invariant verified. Retain as a credible DeFi AMM candidate lead, held pending the constant-sum/StableSwap structural ruling and a frozen two-token rate-provider, target, fee and scaling contract. The earlier concern about a moving-branch-only source is closed by the immutable commit above.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, pool reads or transactions were run. This is static source review only.
