# Core-295 source verification audit 67: Maverick V2 implementation-access and scope limitation

**Date:** 2026-11-11  
**Status:** follow-up to discovery batch 32 for existing source lead AMM-MAVERICK-DYNAMIC. No equation is added to the formal catalogue or counted toward 295.

## 1. Whitepaper invariant remains sourceable

The January 2024 Maverick V2 technical whitepaper draft gives the tick invariant:
\[
L^2=\left(B+\frac{L}{\sqrt{p_u}}\right)
\left(A+L\sqrt{p_l}\right).
\]
This is constant product in virtual reserves:
\[
B_{virt}=B+\frac{L}{\sqrt{p_u}},
\qquad
A_{virt}=A+L\sqrt{p_l},
\qquad
A_{virt}B_{virt}=L^2.
\]
The normalized invariant therefore remains in the same virtual-reserve constant-product family as Gyro 2-CLP and related concentrated-liquidity models. Bin movement, tick merging and dynamic distribution are protocol state transitions, not new invariant equations.

## 2. Implementation pin evidence and access limitation

The Maverick V2 Supplemental Security Review (26 April 2024) identifies:
- repository: github.com/maverickprotocol/maverick-v2;
- reviewed commit: 47287a62e15ca8d4bcabf7e0b6757debb5d10593;
- resolution commit: 175f8c39b19df69134add3aa8a2a042ce3047763.

The audit's stated scope is the v2-supplemental/contracts subtree, excluding LiquidityUtilities.sol, MaverickV2PoolLens.sol, MaverickV2Quoter.sol and PositionImage.sol. It does not establish that the core pool swapping and liquidity-provision equations were validated in the reviewed scope.

The repository is not accessible through the current GitHub repository/API retrieval path (the reported repository URL returns 404). Therefore this review cannot independently fetch the pinned core pool source or verify the whitepaper invariant against executable implementation code. The security audit's commit reference is provenance evidence only; it is not a substitute for the source files.

## 3. TWAP and dynamic-distribution limitations

The whitepaper's tick-domain TWAP is an autoregressive log-price state used by movement-mode bins. The exact recurrence and movement thresholds require a primary implementation transcription and version pin. The current material is insufficient to freeze:
- all TWAP update branches and integer rounding;
- tick/bin migration and merge state transitions;
- liquidity movement and fee accounting;
- exact-in/exact-out swap implementation.

Do not count the whitepaper's invariant, quadratic solution for \(L\), price relation, TWAP recurrence, bin movement, bin merging and liquidity-update operations separately.

## 4. Decision

**Disposition:** retain Maverick V2 as a protocol-architecture/source lead, but keep it held. Its whitepaper invariant is virtual constant product and does not add a new scalar invariant family. The dynamic bin/TWAP system could only be considered as one complete protocol-system unit after core source access, full implementation verification and a declared system-level policy. The prior security review's limited scope does not close the implementation gap.

No source-register or equation-catalogue record was changed. The source register remains 138 records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, pool reads or transactions were run. This is document and repository-access review only.
