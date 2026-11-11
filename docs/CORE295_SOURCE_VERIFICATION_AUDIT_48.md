# Core-295 source verification audit 48: Sky/Maker Liquidations 2.0 Dutch-auction price and liquidation state machine

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead RISK-SKY-COLLATERAL-LIQUIDATION; no equation is added to the formal catalogue or counted toward 295.

## 1. Versioned sources

Official Sky Protocol documentation: Collateral Liquidation, sections on price-versus-time, Dog.bark, Clipper.kick/take/redo, and the liquidation circuit breaker.

Pinned implementation:
- repository: sky-ecosystem/dss
- branch at reviewed revision: liq-2.0
- commit: d5326367a9e1a6bfc4cb74673f934834e06d9da5
- src/clip.sol, blob SHA 96a085848cb26cc5d3232004adcd6782e43253a2
- src/abaci.sol, blob SHA 8aa7fb96cfc5c630512751096d62a3bf551fd917

The docs describe Liquidations 2.0 as a Dutch auction with instant settlement, full-debt transfer into the liquidation system, partial collateral purchases, per-collateral and global auction capacity limits, and a four-stage circuit breaker. The starting price is the delayed OSM price multiplied by governance buffer \(buf\).

## 2. Three price-versus-time calculators

Let \(p_0\) be the initial auction price, \(t\) elapsed seconds, \(R=10^{27}\) the RAY scale.

### Linear decrease

The pinned LinearDecrease implementation returns:
\[
p(t)=
\begin{cases}
p_0\left(1-\frac{t}{\tau}\right),&0\le t<\tau,\\
0,&t\ge\tau.
\end{cases}
\]
The source performs the operation with RAY fixed-point arithmetic and returns zero once elapsed time reaches \(\tau\).

### Stair-step exponential decrease

With per-step multiplier \(c\le R\) and step duration \(\Delta>0\):
\[
p(t)=p_0\,c^{\lfloor t/\Delta\rfloor}.
\]
The code uses fixed-point exponentiation by squaring (rpow) and RAY multiplication. The price is constant within each step and falls at step boundaries.

### Continuous per-second exponential decrease

With per-second multiplier \(c\le R\):
\[
p(t)=p_0\,c^t.
\]
The implementation uses the same fixed-point exponentiation routine. The source explicitly notes that this is mathematically equivalent to the stair-step implementation with \(\Delta=1\), though it is more gas-efficient.

The price calculator is replaceable through the Abacus interface. The linear and exponential forms are genuinely different scalar functions; the stair-step form with \(\Delta=1\) is not a distinct structure from the continuous per-second exponential form.

## 3. Auction state and risk controls

The Clipper status function obtains current price from the configured calculator using elapsed time since auction start. It requires reset when either:
\[
t>tail
\quad\text{or}\quad
\frac{p(t)}{p_0}<cusp.
\]
A reset refreshes the starting timestamp and resets \(p_0\) from the then-current OSM price times \(buf\).

Dog.bark confiscates an undercollateralized Vault's collateral, moves debt into the protocol's bad-debt accounting, and starts a Clipper auction. The global Hole/Dirt and per-collateral ilk.hole/ilk.dirt accumulators constrain the total debt-plus-penalty exposure in active auctions. Clipper.take accepts a partial collateral quantity, calculates the amount owed at the current auction price, caps it at the remaining debt/fee target tab, and preserves the chost minimum residual heuristic.

These controls are coupled to the auction mechanism. They are not independent universal equations.

## 4. Structural classification

This is a versioned Dutch-auction liquidation system with a configurable time-price curve. It is distinct from:
- Euler's health-shortfall reverse-auction discount, which depends on account health rather than elapsed auction time;
- Morpho's capped reciprocal liquidation incentive factor, which depends on LLTV and a cursor;
- Liquity Stability Pool's path-dependent product-sum offset accounting.

Do not count the linear, stair-step and continuous price calculators as three independent observations from the same protocol. The stair-step \(\Delta=1\) case is equivalent to continuous exponential; all calculators, reset rules, partial-take caps, keeper incentives and capacity accumulators are part of one liquidation-auction system family. A cross-protocol comparison of linear versus exponential decay can be recorded as distinct scalar price laws, but it does not create independent protocol/system units.

## 5. Adapter requirements

Freeze:
- exact Dog/Clipper/Abacus implementation revision;
- selected price calculator and all parameters (\(\tau\), or \(c,\Delta\));
- OSM price and timestamp, buf, auction start time and elapsed-time semantics;
- RAY fixed-point arithmetic, rpow rounding and overflow constraints;
- liquidation debt/penalty target tab and collateral lot;
- global and per-collateral Hole/Dirt capacity state;
- tail/cusp reset behavior, chost, partial-take rules and keeper incentives;
- whether the sampled unit is a scalar price curve or the complete liquidation-auction state machine.

## 6. Decision

**Disposition:** official protocol documentation and pinned Dog/Clipper/Abacus implementation verify the configurable Dutch-auction price laws and associated risk controls. Retain as a strong DeFi Risk complete-system lead, held pending the system-unit policy and a frozen auction adapter. Treat linear and exponential scalar functions as different forms if scalar equations are eligible, but do not count multiple Abacus choices or the auction's derived operations as independent samples.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, on-chain reads or transactions were run. This is official-documentation and static-source review only.
