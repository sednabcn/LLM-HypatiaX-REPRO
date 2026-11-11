# Core-295 candidate discovery batch 12: Gyroscope, Bancor and Maverick AMM designs

**Status:** source and implementation tracing only. No equation is accepted or counted toward the 59 DeFi AMM target.

## 1. Gyroscope 2-CLP: quadratic concentrated-liquidity invariant

**Implementation source:** Balancer's balancer-maths repository, typescript/src/gyro/gyro2CLPMath.ts. The captured file blob SHA is 635046fb5a6a498321bba8c1e7233ad0dd1cffd0. The code comments state the invariant quadratic as:

\[
\left(1-\sqrt{\frac{\alpha}{\beta}}\right)L^2
-\left(\frac{y}{\sqrt{\beta}}+x\sqrt{\alpha}\right)L
-xy=0.
\]

The implementation computes the positive root using a numerically arranged quadratic formula and directed fixed-point rounding. An equivalent virtual-offset interpretation is \(L^2=(x+L/\sqrt{\beta})(y+L\sqrt{\alpha})\), with the offsets depending on the invariant itself.

**Boundary:** this is a modified quadratic/virtual-reserve invariant with finite price bounds. It is not the same equation as Uniswap v3's local virtual-reserve constant-product relation, although both use virtual balances. Keep Gyro 2-CLP as one candidate family; the positive-root solver, spot-price calculation and swap-in/out expressions are derived operations, not additional equations. The implementation's exact fixed-point rounding and alpha/beta constraints are part of the model.

## 2. Gyroscope E-CLP: elliptic concentrated-liquidity invariant

**Primary technical specification:** Klages-Mundt & Schuldenzucker (Nov 2022), [E-CLP Technical Overview](https://3407769812-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MU527HCtxlYaQoNazhF%2Fuploads%2F2HscaHAluwXqLel1O4LI%2FE-CLP%20Technical%20Specification.pdf?alt=media&token=e67627c3-61ee-4786-9bca-9f0f5ab6d4d5).

The specification defines the trading curve as a shifted, rotated and stretched ellipse. Its invariant curve is:

\[
( e_x\cdot A(t-(a,b)) )^2+
( e_y\cdot A(t-(a,b)) )^2=r^2,
\]

where \(t=(x,y)\) is the reserve state, \((a,b)\) is the shift/virtual offset, \(A\) is the static deformation matrix built from \(\lambda,s,c\), and \(r\) is the invariant radius. The paper gives the invariant calculation on p. 4:

\[
r=
\frac{A t\cdot A\chi+
\sqrt{(A t\cdot A\chi)^2-(A\chi\cdot A\chi-1)\,A t\cdot A t}}
{A\chi\cdot A\chi-1},
\]

with \(\chi=(e_x\cdot A^{-1}\tau(\beta),\ e_y\cdot A^{-1}\tau(\alpha))\). The same specification provides reserve-solving expressions and the mapping of price bounds to ellipse intersections.

**Implementation cross-check:** Balancer's typescript/src/gyro/gyroECLPMath.ts file snapshot has blob SHA c048a4b2c3606e69e2284f721947a34d49a22f7f. The implementation uses a transformed invariant calculation, high-precision fixed-point arithmetic and explicit error bounds. The invariant, reserve solver, spot-price calculation and conservative rounding are one E-CLP family.

**Boundary:** E-CLP is a distinct ellipse-based candidate, but it shares protocol lineage with Gyro 2-CLP and is implemented within Balancer infrastructure. Record source-family and protocol-family clustering; do not assume the two pools are independent statistical units. Pin the paper revision and exact code commit before acceptance.

## 3. Bancor 2017 constant-reserve-ratio bonding curve

**Primary historical source:** Hertzog, Benartzi & Benartzi, *Bancor Protocol: Continuous Liquidity and Asynchronous Price Discovery for Tokens through their Smart Contracts*, draft v0.99, May 30, 2017; [archived whitepaper copy](https://paperzz.com/doc/9208421/whitepaper---bancor-protocol), p. 11.

The constant reserve ratio is \(F=R/(SP)\), where \(R\) is reserve balance, \(S\) is smart-token supply and \(P\) is price. The purchase return for reserve deposit \(E\) is:

\[
T=S\left[\left(1+\frac{E}{R}\right)^F-1\right],
\]

and the sale return for burning \(T\) smart tokens is:

\[
E=R\left[1-\left(1-\frac{T}{S}\right)^{1/F}\right].
\]

The marginal price can be written \(P=R/(FS)\). These expressions are linked by the same constant-reserve-ratio bonding-curve invariant; purchase, sale, marginal-price and cross-connector formulas are not independent candidates.

**Boundary:** this is an issuance/redemption bonding curve for reserve-backed smart tokens, not a conventional two-sided LP reserve invariant. It is a possible DeFi AMM source family only if the catalogue's domain definition explicitly includes on-chain continuous-token market makers. Keep separate from Bancor's later protocol versions and from Uniswap-style constant-product pools. The whitepaper copy is archived on a third-party host; verify against an official archival copy and the exact contract release before acceptance.

## 4. Maverick dynamic distribution AMM: algorithmic source lead

**Protocol source:** [Maverick AMM dynamic distribution overview](https://medium.com/maverick-protocol/maverick-amm-the-revolutionary-dynamic-distribution-amm-that-enables-directional-lping-unlocking-greater-capital-efficiency). The protocol describes discrete price bins, arbitrary liquidity distributions, and four movement modes (Static, Right, Left, Both). Liquidity positions may shift when the time-weighted average price crosses bin boundaries.

**Implementation-audit pointer:** [Omniscia Maverick AMM audit](https://omniscia.io/reports/maverick-protocol-amm-implementation-660d67630ad02500194e7f43/index.html) identifies formula ranges 10–20 for moving/merging/removing liquidity and 32–39 for bin movement/TWAP. The audit explicitly does not validate the full swap/liquidity formula surface.

**Boundary:** this is presently an algorithmic state-transition source lead, not an accepted closed-form equation. The exact whitepaper revision, deployed contract commit, bin-movement conditions, TWAP crossing rule and invariant accounting must be recovered before a mathematical transcription. Do not treat each movement mode or bin as a separate equation.

## Cross-family overlap controls

- Gyro 2-CLP and Gyro E-CLP are both concentrated-liquidity curves but have distinct quadratic versus elliptic invariants. Keep their mathematical structures separate while clustering their shared protocol lineage and Balancer implementation framework.
- Gyro 2-CLP positive-root solving and Gyro E-CLP invariant-error calculation are numerical implementations, not additional market-making laws.
- Bancor's purchase, sale and spot-price formulas are all consequences of one constant-reserve-ratio bonding curve.
- Bancor's continuous-token issuance curve is not automatically equivalent to a two-token reserve AMM. Confirm that this mechanism fits the predeclared DeFi AMM domain definition before selecting it.
- Maverick's dynamic bin movement is a state machine with incomplete primary formula tracing. Keep it as a discovery lead only until the complete whitepaper/code source is pinned.
- No protocol, version, bin size, parameter choice or algebraic rearrangement should be counted as a structurally distinct equation without an equivalence review.

All source records remain candidates. No DeFi AMM equation is accepted; no experiment or workflow has been run.
