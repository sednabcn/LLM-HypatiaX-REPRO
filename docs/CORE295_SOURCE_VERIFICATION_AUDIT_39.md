# Core-295 source verification audit 39: Gyroscope 2-CLP virtual constant-product invariant

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead AMM-GYRO-2CLP-CODE; no equation is added to the formal catalogue or counted toward 295.

## 1. Source and invariant

Gyroscope's 2-CLP is a two-token concentrated-liquidity pool with lower and upper price bounds \(\alpha,\beta\), \(0<\alpha<\beta\). The pinned implementation source is:
- repository: balancer/balancer-maths
- commit: 4093af0d665b025dc2a3c3f766a4518221914c29
- file: typescript/src/gyro/gyro2CLPMath.ts
- blob SHA: 635046fb5a6a498321bba8c1e7233ad0dd1cffd0

The implementation's quadratic comment gives:
\[
0=
\left(1-\sqrt{\frac{\alpha}{\beta}}\right)L^2
-\left(\frac{y}{\sqrt{\beta}}+x\sqrt{\alpha}\right)L
-xy.
\]
Rearranging:
\[
L^2=
\left(x+\frac{L}{\sqrt{\beta}}\right)
\left(y+L\sqrt{\alpha}\right).
\]
Thus the 2-CLP invariant is constant product in virtual reserves:
\[
x_{virt}=x+\frac{L}{\sqrt{\beta}},
\qquad
y_{virt}=y+L\sqrt{\alpha},
\qquad
x_{virt}y_{virt}=L^2.
\]
The code solves the corresponding quadratic for \(L\) and uses the invariant to compute virtual offsets for swap execution. It uses fixed-point arithmetic and explicit directional rounding.

## 2. Structural comparison

The 2-CLP invariant is not a new algebraic family relative to constant product:
- it is exactly \(xy=k\) after translating each reserve by an invariant-dependent virtual offset;
- Uniswap v3 single-range liquidity uses the same virtual-reserve constant-product principle, though with different parameterization, tick representation, and fixed-point implementation;
- Maverick V2's tick invariant and Curve LLAMMA's per-band invariant are also constant product in virtual reserves.

The finite price bounds \(\alpha,\beta\), concentrated range and liquidity-management architecture are protocol features. They do not change the underlying product form under a strict structural equation policy. The Gyro E-CLP is different: its transformed ellipse invariant is not virtual constant product.

## 3. Decision

**Disposition:** implementation equation and quadratic solver verified. Keep Gyro 2-CLP grouped with the virtual-reserve constant-product family and the Core-15 Constant Product exclusion. Do not count it separately from Uniswap v3, Maverick tick invariants or LLAMMA per-band invariants under a strict algebraic-form rule. Use the E-CLP, not 2-CLP, as the distinct Gyroscope invariant lead.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, pool reads or transactions were run. This is static source review only.
