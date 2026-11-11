# Core-295 candidate discovery batch 32: Maverick V2 dynamic-distribution AMM

**Date:** 2026-11-11  
**Status:** discovery/source-family screen only. No equation is added to the formal catalogue or counted toward 295.  
**Domain focus:** DeFi AMM.

## 1. Primary protocol specification

**Source:** Maverick Research Team, *Maverick v2 – The Liquidity Operating System*, January 2024 technical whitepaper draft.

The whitepaper defines a tick with lower and upper prices (p_l,p_u), aggregate quote reserve (A), aggregate base reserve (B), and tick liquidity (L). Its tick swap invariant (Eq. 1, printed p. 3) is:
[
L^2=\left(B+\frac{L}{\sqrt{p_u}}\right)
\left(A+L\sqrt{p_l}\right).
]
The whitepaper's swapping section derives the equivalent quadratic for (L) (Eq. 29) and the tick price relation (Eq. 31). The pool can have four bin types (Static, Right, Left, Both) per tick; movement-mode bins can move across ticks and merge when they arrive at an occupied bin.

## 2. Structural comparison

The invariant is constant product in virtual reserves:
[
B_{virt}=B+\frac{L}{\sqrt{p_u}},
qquad
A_{virt}=A+L\sqrt{p_l},
qquad
A_{virt}B_{virt}=L^2.
]
This is the same virtual-reserve constant-product structure screened for Gyroscope 2-CLP. The different tick bounds, bin types, movement rules and dynamic liquidity distribution create a distinct protocol architecture, but they do not create a new invariant equation under the current equation-only policy.

Maverick V2 is therefore related to:
- Gyro 2-CLP's constant-product invariant in virtual reserves;
- Uniswap v3's concentrated-liquidity price ranges, though the exact virtual-reserve and liquidity-accounting formulation differs;
- LFJ Liquidity Book's discrete bins and multi-bin traversal at the architecture level, though LFJ's per-bin invariant is constant-sum rather than this virtual constant-product form.

Do not count separate equations for each bin type, each tick, the quadratic solution for (L), price relation, liquidity-add/remove formulas, merge/migration bookkeeping, or exact-in/exact-out swap directions. These are components of the one tick/bin state-transition model.

## 3. TWAP and movement logic

The whitepaper defines its TWAP over (log_{1.0001}) price (tick-domain log price) using a recursive autoregressive update with a finite lookback and capped deviations (Eqs. 40–46). It is not an arithmetic time integral of spot price. The TWAP update also determines whether movement-mode bins shift. This is a separate state variable within the same AMM protocol system, not another invariant equation.

A benchmark would need to freeze:
- tick spacing, price bounds, token orientation and token scaling;
- active tick, bin kind, reserves, liquidity and bin-merge state;
- movement trigger, TWAP lookback, minimum interval and tick-domain log-price convention;
- fee and protocol-fee parameters;
- exact implementation commit, fixed-point rounding and token-balance solvency checks.

The whitepaper is a draft and the external audit report notes that only selected bin-moving/merging and TWAP formula sections were validated against implementation; the swapping and liquidity-provision sections were not in that audit's validated scope. A full implementation verification is therefore still required before even a protocol-specific adapter can be frozen.

## 4. Decision

**Disposition:** retain Maverick V2 as protocol-architecture and implementation research context, but do not add it as a new structurally distinct invariant candidate under the current policy. Its tick invariant is virtual constant product, the same core mathematical family as Gyro 2-CLP. Its dynamic bin movement and autoregressive log-price TWAP are system features; they should not be counted as extra equations without a declared model-level unit policy.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, pool reads or transactions were run. This is whitepaper-level source-family review only.
