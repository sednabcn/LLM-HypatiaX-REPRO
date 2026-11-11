# Core-295 DeFi AMM source expansion and structural screen 1

**Date:** 2026-11-11  
**Branch:** `promotion/rerun-code-review`  
**Scope:** Source discovery and static equation-family screening only. No contracts, validators, generators, solvers, experiments, workflows or live protocol calls were run.

## Result

Three source records were added to the DeFi AMM source register and bibliography:

- `AMM-JOE-LB-WP-2022`: Trader Joe JOE v2.1 Liquidity Book design paper.
- `AMM-YIELDSPACE-WP-2020`: YieldSpace constant power-sum invariant paper.
- `AMM-INVARIANT-WP-2021`: Invariant concentrated-liquidity whitepaper.

The register now contains **159 source records**: Chemistry 32, Biology 30, Physics 43, DeFi AMM 23, DeFi Risk 31. These are source records, not equations. The Core-295 manifest remains draft; 19 proposed equation entries remain proposed and zero are accepted. The sampling frame remains unfrozen.

## Source-grounded structural findings

### 1. Trader Joe Liquidity Book

The JOE v2.1 paper (November 2022) defines a bin-level reserve relation (P_i x+y=L) (Eq. 2.2), where (P_i) is fixed for a bin and (L) is its conserved nominal reserve value. It also defines composition (c=y/L), aggregate-bin market structure, and geometric bin prices (P_i=(1+s)^{i-b}) (Eq. 3.3). The paper explicitly characterizes each bin as a constant-sum market.

**Screen:** The isolated bin equation is a weighted/fixed-price constant-sum relation, not a new structural equation relative to the general constant-sum form. Under the draft E0–E5 policy, do not count the bin equation alone as structurally distinct. The aggregate discrete-bin market and state-transition rules may form a separate *protocol-level dynamical model*, but that is not established by counting Eq. 2.2 repeatedly. Any future candidate must specify the full state, transition conditions, bin crossing, fees, rounding, and a pinned implementation version.

### 2. YieldSpace

Niemerg, Robinson and Livnev (August 2020 working draft, rev. 1) introduce the constant power-sum invariant
[
x^{1-t}+y^{1-t}=k
]
with normalized time-to-maturity (t) (Eq. 1). The paper explains that (t=0) gives the constant-sum relation and the limit (t\to1) approaches constant product. It also gives the pool's marginal interest-rate relation in Eq. 2.

**Screen:** This is a stronger structurally distinct lead than a fee/swap rearrangement: the governing invariant has a time-to-maturity-dependent exponent and a fixed-yield-token market mechanism. Keep it as a candidate family, not an accepted entry. A benchmark contract must specify token orientation, maturity normalization, admissible (t), reserve positivity, units/scaling, fee treatment, and whether the target is the invariant or a complete swap/state-transition map. The endpoint cases are not additional equations.

### 3. Invariant concentrated-liquidity AMM

Cichocki's 2021 whitepaper states the reserve curve (xy=L^2) and obtains a bounded-range position by translating virtual reserves. This is the same constant-product reserve geometry used by Uniswap v3 concentrated liquidity; a different chain/deployment or a translated coordinate system does not by itself create a new invariant.

**Screen:** Use this source as independent implementation/context evidence for the Uniswap-v3-style family, not as an additional structural-equation candidate. Its range-specific reserve formulas are derived from the translated constant-product curve and should remain grouped with that family under the current draft policy.

## Consequences for the candidate pool

- Do not add the three source records as three equation entries.
- YieldSpace is a high-priority candidate lead for full equation reconstruction and a protocol-version trace.
- Liquidity Book's per-bin constant-sum equation is not a separate structural count; its aggregate state machine remains a research lead only.
- Invariant's concentrated-liquidity formulas remain grouped with Uniswap v3.
- This screen applies the *draft* equivalence policy consistently as a provisional audit judgement; it does not freeze the policy or alter formal acceptance status.

## Sources

- Trader Joe, *JOE v2: Liquidity Book*, November 2022, §§2.1–2.4, 3.1–3.3: https://resources.cryptocompare.com/asset-management/333/1669892646295.pdf
- Niemerg, Robinson & Livnev, *YieldSpace*, August 2020, Eq. 1–2 and §2: https://yieldprotocol.com/YieldSpace.pdf
- Cichocki, *Invariant*, 6 December 2021, §2: https://invariant.app/whitepaper.pdf

The source records and bibliography entries are discovery references only. No candidate is accepted by this document.
