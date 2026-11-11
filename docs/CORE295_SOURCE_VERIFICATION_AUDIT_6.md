# Core-295 source verification audit 6: LFJ Liquidity Book discrete-bin AMM

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** the existing AMM-LFJ-LIQUIDITY-BOOK source lead. The review compares the November 2022 JOE v2.1 whitepaper with a pinned implementation snapshot; it does not execute contracts or make protocol calls.

## 1. Primary model: discrete constant-price bins

The JOE v2.1 *Liquidity Book* whitepaper (November 2022) describes a market as liquidity distributed across discrete price bins. Each bin exchanges reserves at one fixed price; the market aggregates the bins and moves through adjacent nonempty bins as a swap exhausts liquidity.

The whitepaper defines price as the rate of change in Y reserves per X reserve (Eq. 2.1) and bin liquidity as the constant-sum value

\[
L_i=P_i x_i+y_i
\]

(Eq. 2.2). The composition factor is c_i=y_i/L_i (Eq. 2.3), giving y_i=c_i L_i and x_i=(L_i/P_i)(1-c_i) (Eqs. 2.4–2.5). At a fixed bin price, reserve exchange obeys

\[
\Delta y_i=-P_i\Delta x_i
\]

(Eq. 4.5), while composition changes according to the corresponding reserve-flow relations (Eqs. 4.6–4.7). The bin price grid is geometric:

\[
P_i=(1+s)^{i-b},\qquad b=2^{23},
\]

where s is the fractional bin step (Eqs. 3.2–3.3). The paper states that bin liquidity is constant as reserve composition changes and that the market price is associated with the lowest bin containing X reserves.

This is a discrete, piecewise-constant-price liquidity architecture. It is not the Uniswap v2 constant-product invariant, and it is not Uniswap v3's continuous constant-product position curve. The whitepaper itself contrasts LB's discretized concentrated liquidity with the common constant-function approach used by Uniswap and Curve.

## 2. Implementation cross-check

A static source inspection was made against the immutable joe-v2 repository commit 067c6ccf5b8ff1526d03fa3e4c65ec45d01c1f73 (not a live contract call):

- src/libraries/BinHelper.sol defines bin liquidity using the constant-sum expression L = price*x + y.
- BinHelper.getAmounts computes the maximum input required to exhaust the output-side reserve of one bin, applies the fee, computes output at that bin's fixed price, and uses integer rounding in the appropriate direction.
- src/libraries/PriceHelper.sol computes the bin price from the bin identifier and bin step using a 128.128 fixed-point base equivalent to 1 + binStep/10,000 and exponent id - 2^23.
- src/LBPair.sol iterates across nonempty bins during swaps, updates the active bin and volatility accumulator, and updates the oracle after the swap.

The implementation therefore confirms the whitepaper's central design, but the benchmark cannot use the real-number equations alone if it claims implementation-level reproduction. Fixed-point scaling, token decimal conventions, rounding direction, fee calculation, bin traversal, active-bin state and the selected contract revision all affect outputs.

## 3. Fees and state are part of the protocol, not separate equation candidates

The whitepaper's fee subsystem includes:
- base fee proportional to bin step (Eq. 4.9);
- a variable fee quadratic in volatility accumulator times bin step (Eq. 4.10);
- a volatility accumulator based on crossed-bin distance and a time-decayed reference (Eqs. 4.11–4.13);
- protocol fee share (Eq. 4.15).

These are coupled parts of one protocol state/transition model. Do not count the bin price grid, constant-sum bin relation, per-bin swap equation, fee equation and volatility accumulator as five independent equations merely because they have separate labels. The whole market is a discrete state machine over bin reserves, active ID, fee parameters and time-dependent volatility state.

## 4. Structural-family assessment and eligibility

The constant-sum per-bin relation is structurally different from the Core-15-excluded constant-product invariant. The geometric bin-price grid and discrete traversal produce a market architecture distinct from continuous concentrated-liquidity positions. This is a strong DeFi AMM candidate family, subject to the catalogue's policy for system-level/state-machine units.

The source family should include the per-bin constant-sum accounting, geometric price indexing and market traversal as one Liquidity Book model. Alternative bin IDs, bin-step values, swap directions, per-bin versus aggregated outputs, and fee-free versus fee-enabled variants are not automatically independent equations.

### Required before a proposed catalogue record can be completed

1. Pin the intended protocol version and contract commit; the immutable implementation inspected here is commit 067c6ccf5b8ff1526d03fa3e4c65ec45d01c1f73.
2. Decide whether the benchmark unit is the whole multi-bin swap/state-transition model or a restricted fee-free bin-level model. Do not mix the two.
3. If implementation fidelity is intended, specify 128.128 price representation, token scaling/decimals, integer rounding, fee parameterization, bin traversal and oracle/volatility state.
4. Freeze valid bin-step, active-ID, reserve, fee and volatility parameter domains from the chosen version.
5. Assign a source-family ID and a statistical-unit policy that does not treat each bin or each swap direction as independent evidence.

The source lead remains held and is not counted toward the 59-per-domain target by this audit.

## 5. Work not performed

No contracts were deployed or called. No transaction, simulation, experiment, validator, solver, workflow, paid compute or live API/protocol action was run. No formal catalogue entry or source status was changed.
