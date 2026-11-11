# Core-295 source verification audit 42: Solidly stable-pool quartic invariant

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead AMM-SOLIDLY-STABLE-V2; no equation is added to the formal catalogue or counted toward 295.

## 1. Pinned implementation and exact invariant

The Solidly stable-pool specification states that stable pools use the curve \(x^3y+xy^3=k\), while volatile pools use \(xy=k\). The original Solidly repository documentation also describes the new stable curve as \(x^3y+y^3x\).

Pinned implementation inspected:
- repository: velodrome-finance/solidly
- commit: eac1ef02ca8736138b25062c02646ea43d5bb6e4
- file: contracts/BaseV1-core.sol
- blob SHA: c140e29568c656d9499a4edd17ac0e707bb020b8

The implementation's _k function normalizes each reserve to 1e18 units using its token decimals:
\[
X=x\frac{10^{18}}{d_0},
\qquad
Y=y\frac{10^{18}}{d_1}.
\]
It then computes:
\[
k=\frac{XY}{10^{18}}\cdot
\frac{X^2+Y^2}{10^{18}}
\]
with fixed-point scaling, equivalent in real arithmetic to:
\[
k=XY(X^2+Y^2)=X^3Y+XY^3.
\]
The source comment explicitly identifies \(x^3y+y^3x\geq k\). The volatile branch computes \(xy\).

## 2. Mathematical and protocol interpretation

The stable invariant is a symmetric homogeneous quartic polynomial. It is designed for two assets expected to remain close in value, with lower slippage near the balanced 1:1 region than the constant-product curve. The normalized reserve variables are important: raw token units with different decimals cannot be substituted directly.

The contract's swap solver uses the pre-swap invariant as target \(k\), updates the input reserve after fee, then solves for the output reserve \(y\) such that the same stable invariant is maintained. The exact-in/out swap functions, cubic/quartic solving steps, reserve update, LP mint/burn and stable/volatile flag are operations on one pool model, not separate equations.

## 3. Structural comparison

The Solidly stable invariant is structurally distinct from:
- constant product \(xy=k\);
- Balancer positive-weight geometric invariant;
- Curve StableSwap's finite-amplification implicit invariant;
- Curve CryptoSwap's dynamic-\(K\) amplified invariant;
- DODO's inventory-dependent PMM;
- Gyro E-CLP's ellipse;
- Balancer Linear Pool's rate-normalized constant-sum invariant.

It is one stable-swap family across Solidly-derived forks (Velodrome, Aerodrome, Camelot and other implementations). Forks, token decimal scales, fee values and parameterizations do not create independent equation candidates.

The invariant is not a special case of Curve StableSwap obtained by merely changing amplification: its normalized quartic polynomial is different. It shares the broad purpose of low-slippage correlated-asset exchange but has no StableSwap amplification parameter.

## 4. Acceptance adapter and validity contract

A deterministic adapter must freeze:
- exact Solidly-derived implementation and commit;
- stable vs volatile pool flag;
- token order, token decimals and normalized reserve units;
- fee scale and fee deduction order;
- reserve positivity and maximum values avoiding overflow;
- exact integer/fixed-point rounding and solver iteration/convergence behavior;
- valid stable-pair price regime and whether the invariant is used only near 1:1 or across the full reserve domain.

The polynomial is homogeneous of degree four, so equal scaling of normalized reserves scales \(k\) by the fourth power. The implementation's decimal normalization must be preserved to reproduce the protocol.

## 5. Decision

**Disposition:** primary protocol specification and pinned implementation correspondence verified. Retain as a strong DeFi AMM candidate lead: the normalized quartic \(XY(X^2+Y^2)=k\) is structurally distinct from the reviewed CP, weighted, StableSwap/CryptoSwap, PMM, ellipse and linear-sum invariants. Treat all Solidly-derived stable-pool forks as one family. Hold pending a deterministic normalized-reserve/fee/solver adapter; do not add a formal proposed record or accept it in this audit.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, pool reads or transactions were run. This is static source review only.
