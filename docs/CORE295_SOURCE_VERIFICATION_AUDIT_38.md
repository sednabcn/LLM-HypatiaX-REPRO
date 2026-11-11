# Core-295 source verification audit 38: Gyroscope Elliptic Concentrated Liquidity Pool invariant

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead AMM-GYRO-ECLP-2022; no equation is added to the formal catalogue or counted toward 295.

## 1. Primary mathematical specification

Ariah Klages-Mundt and Steffen Schuldenzucker, *Elliptic Concentrated Liquidity Pool (E-CLP): Technical Overview*, November 2022, pp. 1–4.

The specification defines:
- lower and upper price bounds \(\alpha>0\), \(\beta>\alpha\);
- stretch factor \(\lambda\geq1\), with \(\lambda=1\) giving a circle;
- rotation angle \(\phi\), represented by \(c=\cos(-\phi)\), \(s=\sin(-\phi)\), with \(c,s\geq0\);
- a rotation point \((c,s)\) normalized to the unit circle;
- current reserves \(t=(x,y)\);
- shifted ellipse center \((a,b)\);
- invariant \(r\), the minor radius of the transformed ellipse.

The transformation matrix is:
\[
A=
\begin{pmatrix}
c/\lambda&-s/\lambda\\
s&c
\end{pmatrix}.
\]
The E-CLP trading curve is defined by the transformed-circle invariant:
\[
\left(\mathbf e_x\cdot A(t-(a,b))\right)^2
+\left(\mathbf e_y\cdot A(t-(a,b))\right)^2
=r^2.
\]
Equivalently:
\[
\|A(t-(a,b))\|_2^2=r^2.
\]
The center \((a,b)\) and radius \(r\) are chosen so that the ellipse passes through the current reserve state and has the specified lower/upper price bounds. The slope of the tangent gives the negative of the asset-x price in units of asset-y. The specification gives a closed-form expression for \(r\) from the current reserves and derived parameter vector.

The invariant is an ellipse after an affine shift, anisotropic stretch and rotation. It is not the Gyro 2-CLP quadratic/virtual-constant-product curve. E-CLP permits asymmetric concentration and nonuniform liquidity over the price range.

## 2. Pinned implementation correspondence

The implementation snapshot is:
- repository: gyrostable/gyro-pools
- commit: 7624ca2a78b22698e11a9b3be88ceaadf7181657 (14 October 2026)
- contracts/eclp/GyroECLPMath.sol, blob SHA 73a2aedbd6f958e15ee3255ff8374c2ffc80c8fa
- contracts/eclp/GyroECLPPool.sol, blob SHA d02e16349321179af89422dc539763426aada771

The pinned math source defines ECLP Params with \(\alpha,\beta,c,s,\lambda\), and DerivedParams with \(\tau_\alpha,\tau_\beta,u,v,w,z,dSq\). It implements:
- calculateInvariantWithError, computing the transformed ellipse invariant and a conservative numerical-error estimate;
- calcInvariantSqrt, calculating the square-root term of the transformed ellipse;
- calcAtAChi and calcAChiAChiInXp, evaluating the transformed geometry in extra precision;
- calcYGivenX / calcXGivenY and solveQuadraticSwap, solving the other reserve along the same invariant;
- calcOutGivenIn / calcInGivenOut, wrapping the reserve solve with asset-bound checks.

The implementation explicitly handles signed intermediate coordinates, since transformed/shifted circle coordinates can be negative. It uses 18-decimal and 38-decimal fixed-point representations, conservative rounding and error bounds. The pool constructor accepts both immutable ECLP parameters and derived high-precision parameters; the documentation says consistency of the derived parameters is the deployer's responsibility.

## 3. Structural-family classification

E-CLP is structurally distinct from:
- constant product and virtual-reserve constant product (Uniswap v2/v3, Gyro 2-CLP, Maverick and per-band LLAMMA);
- positive-weight geometric invariant (Balancer weighted pools);
- fixed-amplification StableSwap and dynamic-\(K\) CryptoSwap;
- inventory-dependent DODO PMM;
- discrete-bin constant-sum Liquidity Book;
- rate-normalized linear constant-sum pools.

The ellipse can be calibrated to resemble StableSwap-like or constant-product-like liquidity profiles, but the invariant itself remains an affine-transformed ellipse. Approximation of another curve's liquidity profile is not algebraic identity.

The lower/upper price bounds, stretch, rotation, center, radius and current reserve state are parameters/state of one E-CLP invariant. Do not count the invariant radius formula, reserve solve, price derivative, swap-in/out functions, liquidity update or parameter-precomputation functions as independent equations.

## 4. Acceptance adapter and numerical requirements

A deterministic E-CLP adapter must freeze:
- two-token order and reserve units;
- price bounds \(\alpha,\beta\), stretch \(\lambda\), rotation \((c,s)\);
- consistency/normalization of \(c^2+s^2\), \(\tau_\alpha,\tau_\beta\) and derived parameters;
- valid reserve region and price-bound checks;
- signed-coordinate conventions and the definition of tangent price;
- fixed-point scales (18/38 decimals), rounding direction, square-root tolerance and invariant error bounds;
- exact pool version and liquidity-update/swap fee behavior.

The source specification and pinned implementation provide a credible versioned contract. It remains necessary to choose whether the benchmark samples only the static invariant or the complete pool including liquidity updates, fees, rate providers and BPT accounting.

## 5. Decision

**Disposition:** primary mathematical specification and pinned implementation correspondence verified. Retain as a strong DeFi AMM candidate lead: the E-CLP ellipse is structurally distinct from Gyro 2-CLP and other reviewed invariant families. Hold pending a frozen two-token parameter/range generator and explicit static-invariant versus full-pool adapter choice. Do not create or accept a formal equation record in this audit.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, pool reads or transactions were run. This is mathematical-specification and static-source review only.
