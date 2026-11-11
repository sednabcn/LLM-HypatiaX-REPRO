# Core-295 source verification audit 37: Curve CryptoSwap dynamic-peg invariant

**Date:** 2026-11-11  
**Status:** verification of an existing DeFi AMM source-register lead; no equation is added to the formal catalogue or counted toward 295.  
**Scope:** AMM-CURVE-CRYPTOSWAP-WP, Curve CryptoSwap whitepaper and Tricrypto implementation.

## 1. Primary whitepaper invariant

Curve's *Automatic market-making with dynamic peg* / CryptoSwap whitepaper (9 June 2021) defines a dynamic-peg invariant. For \(N\) normalized coin balances \(x_i\), invariant \(D\), amplification \(A\), and concentration parameter \(\gamma>0\):
\[
K_0=\frac{N^N\prod_{i=1}^{N}x_i}{D^N},
\qquad
K=A K_0\frac{\gamma^2}{(\gamma+1-K_0)^2},
\]
and the invariant equation is:
\[
K D^{N-1}\sum_{i=1}^{N}x_i+\prod_{i=1}^{N}x_i
=K D^N+\left(\frac{D}{N}\right)^N.
\]
The pool solves this implicit relation for \(D\). \(A\) controls the central amplification/concentration and \(\gamma\) controls the breadth of the concentrated-liquidity region. The whitepaper describes the invariant as an extension of StableSwap that combines stable-swap-like depth near the price scale with constant-product-like behavior farther away.

## 2. Pinned Tricrypto implementation correspondence

The fetched implementation snapshot is:
- repository: curvefi/curve-crypto-contract
- commit: d7d04cd9ae038970e40be850df99de8c1ff7241b (29 June 2022)
- file contracts/tricrypto/CurveCryptoMath3.vy, blob SHA 1fdd95b2c2b7abe0cca817a41573c04baf7d4125
- file contracts/tricrypto/CurveCryptoSwap.vy, blob SHA 5c9cca8f3f98f798e1aad7da76f188b1d620454a

The Tricrypto math contract sets \(N=3\), uses \(ANN=A N^N\) with a fixed-point A multiplier, calculates:
\[
K_0=\frac{N^N x_1x_2x_3}{D^N}
\]
in 1e18-scaled arithmetic, and iteratively updates \(D\) using Newton's method. The source explicitly checks A, gamma, balance ratios and D bounds; it initializes D from the geometric-mean/constant-product scale and stops at a fixed convergence tolerance. The implementation's integer arithmetic, rounding and convergence checks are part of the executable model.

The pool normalizes balances using token precisions and internal price scales before applying the invariant. A and gamma may be ramped over time; price_scale is an internal state adjusted by an EMA/repegging process. Therefore the whitepaper invariant is not a direct function of raw token balances alone.

## 3. Structural comparison

CryptoSwap is mathematically distinct from:
- constant product \(xy=k\);
- Balancer's positive-weight geometric invariant;
- the fixed-amplification StableSwap invariant;
- DODO's inventory-dependent PMM;
- Gyro E-CLP's elliptical invariant;
- LFJ Liquidity Book's per-bin constant-sum exchange.

It is, however, explicitly related to StableSwap: the dynamic \(K(K_0,\gamma,A)\) term modifies the StableSwap-style implicit invariant to concentrate liquidity around an adaptive price scale and move toward constant-product behavior away from the peg. It should be treated as a distinct parameterized invariant within a broader amplified/stable-swap family, not as an unrelated AMM family.

Do not count the following separately:
- \(K_0\), \(K\) and \(D\) as three equations;
- the implicit invariant and its Newton iteration;
- \(D\)-solver and \(y\)-solver;
- spot-price derivatives and swap in/out formulas;
- A/gamma ramping, price_scale EMA and repegging;
- two-coin and three-coin token-count variants.

These are components and numerical/state-transition operations of one CryptoSwap model family.

## 4. Benchmark contract and blockers

A deterministic adapter must freeze:
- exact pool version and coin count (this audit pins Tricrypto, \(N=3\));
- normalized balances \(x_i\), token precision and price_scale conventions;
- A and gamma units, allowed ranges and whether they are fixed or time-ramped;
- invariant D root-selection and Newton initial guess, iteration limit, convergence tolerance and integer rounding;
- price_scale EMA, allowed extra profit, adjustment_step and repegging rules if the full dynamic-peg system is included;
- fee and fee_gamma behavior;
- valid balance ratios and safety bounds from the selected implementation.

The invariant equation alone is not the entire pool state transition. If the benchmark uses a static invariant-only adapter, it must explicitly hold price_scale, A and gamma fixed and must not claim to reproduce dynamic repegging.

## 5. Decision

**Disposition:** primary whitepaper invariant and pinned Tricrypto implementation correspondence verified. Retain as a strong DeFi AMM candidate lead, held pending exact static-vs-dynamic model scope and deterministic fixed-point/Newton adapter. It is structurally distinct from fixed StableSwap but belongs to the same broader amplified-invariant family. Do not add a formal proposed record or accept it yet.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, live API calls, pool reads or transactions were run. This is whitepaper and static source review only.
