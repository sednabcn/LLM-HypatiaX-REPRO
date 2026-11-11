# Core-295 source verification audit 41: Curve LLAMMA per-band invariant and pinned AMM implementation

**Date:** 2026-11-11  
**Status:** verification of discovery-batch 38 lead only. No equation is added to the formal catalogue or counted toward 295.

## 1. Primary whitepaper equation

Curve's *crvUSD / LLAMMA Summary* technical paper gives, for one band:
\[
\left(\frac{p_o^2}{p_\uparrow}Ay_0+x\right)
\left(\frac{p_\uparrow}{p_o}(A-1)y_0+y\right)
=p_oA^2y_0^2. \tag{6}
\]
The paper defines \(x\) as borrowed-token balance, \(y\) as collateral balance, \(p_o\) as oracle price, \(p_\uparrow\) as the upper band price, \(A\) as band-width factor and \(y_0\) as a virtual collateral offset. It derives a quadratic for \(y_0\) in Eq. (7) and the band price from the derivative in Eq. (8).

The band boundaries are:
\[
p_\uparrow(n)=p_{base}\left(\frac{A-1}{A}\right)^n,\qquad
p_\downarrow(n)=p_{base}\left(\frac{A-1}{A}\right)^{n+1}. \tag{11}
\]

## 2. Pinned implementation correspondence

The fetched current LlamaLend V2 AMM source is:
- repository: curvefi/curve-stablecoin
- commit: f574bd502530fb3353e7b60918e246e50de5891f
- file: curve_stablecoin/AMM.vy
- blob SHA: d14d0329c145d7c5d3e1c61301c93b072184ba02
- source declares Vyper 0.4.3 and title “LlamaLend V2 AMM”.

The implementation's _get_y0 function documents and solves the quadratic:
\[
p_o A y_0^2
-y_0\left(\frac{p_\uparrow}{p_o}(A-1)x+\frac{A p_o^2}{p_\uparrow}y\right)
-xy=0.
\]
This is the rearrangement of whitepaper Eq. (6). The function uses integer square root and fixed-point 1e18 arithmetic. The _get_p function uses the same virtual offsets \(f(y_0)\), \(g(y_0)\) to calculate marginal price:
\[
p=\frac{f(y_0)+x}{g(y_0)+y},
\quad
f(y_0)=\frac{A y_0 p_o^2}{p_\uparrow},
\quad
g(y_0)=\frac{(A-1)y_0p_\uparrow}{p_o},
\]
under the contract's scaling conventions.

This confirms that the whitepaper's band invariant is implemented as a virtual-reserve constant-product relation. The code's current-price and oracle-price boundaries are distinct: the band grid is oracle-defined, while the AMM marginal price depends on the band balances and active-band state.

## 3. Structural classification

The per-band equation is a product of two affine virtual-balance terms. It is therefore structurally related to:
- Gyro 2-CLP's virtual-reserve constant-product invariant;
- Uniswap v3's concentrated-liquidity virtual reserves;
- Maverick V2's tick invariant in virtual reserves.

It is not a new per-band invariant structure under strict normalized-form equivalence. The protocol-level soft-liquidation mechanism is more distinctive:
- user collateral is allocated over multiple price bands;
- oracle price and AMM price create arbitrage incentives;
- declining price gradually converts collateral into borrowed asset;
- rising price can reverse conversion, but previously incurred fees and arbitrage losses remain;
- the controller, interest-rate multiplier, oracle, active band and hard-liquidation health checks interact with the AMM.

The full lending/liquidation state machine may be a separate DeFi Risk system unit, but only if the policy permits complete protocol state-transition systems and the adapter includes all coupled states. The static per-band invariant alone does not model soft liquidation.

## 4. Adapter requirements

Freeze the exact LlamaLend V2 implementation, token order (borrowed asset \(x\), collateral \(y\)), oracle price and base-price convention, interest-rate multiplier, A and band count, user band allocation, active/min/max bands, per-band balances, virtual \(y_0\), dynamic fee, admin fee, fixed-point rounding, arbitrage assumptions and hard-liquidation boundary.

Do not conflate crvUSD LLAMMA V1, LlamaLend V1 and LlamaLend V2; the docs identify different implementation generations. The commit above is specifically the fetched V2 AMM file.

## 5. Decision

**Disposition:** whitepaper Eq. (6) and the V2 AMM implementation's quadratic/price calculations verified. Keep the per-band invariant in the virtual-constant-product family; do not count it as a new AMM invariant beside Gyro 2-CLP, Uniswap v3 or Maverick. Retain the complete multi-band soft-liquidation/de-liquidation mechanism as a possible DeFi Risk system lead, held pending a declared system-level unit policy and deterministic adapter.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, on-chain reads or protocol transactions were run. This is whitepaper and static-source review only.
