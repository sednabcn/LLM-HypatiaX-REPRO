# Core-295 source verification audit 12: Gyroscope E-CLP/2-CLP and Solidly V2 stable invariant

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing DeFi AMM source-register leads. The E-CLP primary technical specification, registered 2-CLP math snapshot, official Solidly documentation and available source/implementation evidence were compared. No on-chain queries or protocol calls were made.

## 1. Gyroscope E-CLP: elliptic concentrated-liquidity invariant

### 1.1 Primary specification

Klages-Mundt and Schuldenzucker, *Elliptic Concentrated Liquidity Pool (E-CLP): Technical Overview*, November 2022. The specification defines an AMM whose trading curve is a selected portion of an ellipse. The ellipse is a shifted, stretched and rotated deformation of a circle.

The exogenous parameters include:
- α > 0 and β > α: lower and upper price bounds;
- λ ≥ 1: stretch factor;
- ϕ: rotation angle, represented through (s=sin(-ϕ)), (c=cos(-ϕ));
- current reserve vector (t=(x,y)), shifting offset ((a,b)), and invariant radius (r).

The transformation matrix in the specification is
[
A=
egin{pmatrix}
c/lambda & -s/lambda\
s & c
end{pmatrix}.
]
The invariant curve is
[
left(e_xcdot A(t-(a,b))ight)^2+
left(e_ycdot A(t-(a,b))ight)^2=r^2.
]
The invariant (r) is the radius in the transformed circle coordinates (equivalently the semi-minor-axis convention described in the specification). The offsets and axis intersections are chosen so that the ellipse passes through the current reserve state and its endpoint prices match α and β.

The paper also supplies a closed-form calculation of (r) from the reserve state and a reserve-solving equation for (x) or (y) at fixed (r). The swaps use the same ellipse; `calculateInvariant`, `calcOutGivenIn`, `calcInGivenOut`, `calcXGivenY`, `calcYGivenX` and balanced liquidity updates are implementation operations on that one curve, not separate equation candidates.

### 1.2 Structural comparison

The E-CLP's rotated/stretched ellipse is not an algebraic rearrangement of the constant-product invariant, the StableSwap sum/product invariant, or the Gyro 2-CLP virtual-reserve construction. It is a credible distinct invariant structure. It remains in the broader Gyroscope/Balancer concentrated-liquidity source lineage and shares market, token and protocol dependencies with the 2-CLP family.

The current source-register entry has the mathematical specification but does not yet pin the deployed contract version/commit that implements the same parameterization. The benchmark adapter must freeze:
- α, β, λ, rotation/normalization parameters and valid ordering;
- token order, reserve units and price orientation;
- ellipse endpoint and admissible reserve constraints;
- exact implementation version, fixed-point precision, conservative error bounds and rounding;
- whether the target is invariant radius, swap output, or a complete deterministic state transition.

**Disposition:** strong, structurally distinct DeFi AMM lead; held pending exact deployed implementation pinning and full parameter/rounding contract.

## 2. Gyroscope 2-CLP: quadratic virtual-reserve construction

The registered `balancer-maths` source snapshot (`typescript/src/gyro/gyro2CLPMath.ts`, blob SHA `635046fb5a6a498321bba8c1e7233ad0dd1cffd0`) documents the invariant calculation through the quadratic:
[
0=left(1-sqrt{alpha/eta}ight)L^2
-left(rac{y}{sqrt{eta}}+xsqrt{alpha}ight)L-xy.
]
Rearranging gives
[
left(x+rac{L}{sqrt{eta}}ight)
left(y+Lsqrt{alpha}ight)=L^2.
]
This is a constant-product invariant in virtual reserves, with offsets determined by the liquidity parameter and the configured price range. The code uses a quadratic root and fixed-point rounding to compute the invariant and swap offsets.

**Disposition:** do not count Gyro 2-CLP as a new structurally distinct equation under the current equation-only policy. Its concentrated price range and virtual-reserve architecture are meaningful protocol design features, but the invariant is a constant-product form after a reserve translation. The Core-15 Constant Product exclusion therefore blocks it absent a separately justified policy that explicitly treats translated virtual-reserve invariants as distinct. Do not count the quadratic solution, virtual-offset calculations, swap directions or invariant initialization as separate equations.

## 3. Solidly V2 stable-pool invariant

### 3.1 Official definition

Solidly's official V2 swap documentation distinguishes:
- volatile pools: (xygeq k);
- stable pools: (x^3y+xy^3geq k).

The stable pool is intended for directly correlated assets; the volatile pool uses the constant-product curve. The two stable-pool coordinates must be interpreted in the protocol's normalized reserve units, not blindly as raw token base units.

The corresponding homogeneous degree-four invariant can be written
[
k=(xy)(x^2+y^2)=x^3y+xy^3.
]
A Solidly-family implementation example normalizes reserves using each token's decimals before evaluating this expression and solves the output reserve numerically while preserving the pre-swap invariant. That confirms why decimal normalization and implementation version are part of the model contract, not optional display details.

### 3.2 Structural and source-family review

The quartic polynomial is structurally distinct from:
- the Core-15-excluded constant-product invariant (xy=k);
- Curve StableSwap's amplification-dependent implicit sum/product invariant;
- Curve CryptoSwap's dynamic-(K), dynamic-peg invariant.

The stable and volatile swap branches are not two independent Solidly candidates: the volatile branch is the excluded constant-product model, while the stable branch is one polynomial invariant. Swap directions, Newton iterations, derivative expressions and decimal-normalization helpers are not additional equation entries.

The official Solidly documentation provides the mathematical invariant, but the current source-register record does not yet freeze a specific original Solidly contract commit, chain/fork or pool implementation. Later forks can preserve the quartic curve while changing fee handling, reserve scaling, decimal normalization and rounding. A benchmark adapter must therefore pin the exact pool/factory version and its (10^{18})-normalized reserve convention, token decimals, swap fee, numerical solver and rounding behavior.

**Disposition:** credible structurally distinct stable-AMM invariant lead; held pending original implementation/version pinning and normalization/rounding contract. The volatile branch is excluded and must not be counted.

## 4. Cross-candidate conclusions

| Lead | Structural result | Disposition |
|---|---|---|
| Gyro E-CLP | Shifted, stretched and rotated ellipse; distinct from CP/StableSwap | Hold; pin deployed implementation and numerical contract |
| Gyro 2-CLP | Constant product in virtual reserves after translation | Exclude as a new equation under current Core-15 policy |
| Solidly V2 stable | Homogeneous quartic (x^3y+xy^3) invariant | Hold; pin original contract/fork and decimal/rounding contract |

These are related by the broad AMM/concentrated-liquidity source universe, not by a single algebraic family. The E-CLP and 2-CLP share Gyroscope lineage; Solidly stable belongs to a separate polynomial stable-swap lineage. Distinct formulas alone do not establish independent statistical units.

## 5. Catalogue and experiment status

No catalogue record, source status, proposed count or accepted count was changed by this audit. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, live API calls, oracle queries, on-chain reads or protocol transactions were run. This is source and static implementation review only.
