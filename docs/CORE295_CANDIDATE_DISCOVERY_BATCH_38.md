# Core-295 candidate discovery batch 38: Curve LLAMMA banded soft-liquidation AMM

**Date:** 2026-11-11  
**Status:** discovery-only source lead. Not added to the formal catalogue or counted toward 295.  
**Domain focus:** DeFi Risk / DeFi AMM.

## 1. Primary protocol model and per-band invariant

**Sources:**
- Curve, *crvUSD / LLAMMA* stablecoin design whitepaper.
- Curve Knowledge Hub, LLAMMA explainer and AMM technical reference.
- Curve LlamaLend V2 AMM docs, which identify a pinned implementation excerpt at commit 0d726b1.

LLAMMA (Lending-Liquidating AMM Algorithm) distributes borrower collateral and borrowed asset across discrete price bands. When the oracle price moves into a borrower's band range, arbitrage trades gradually convert collateral into the borrowed asset (soft liquidation). If price recovers, the conversion can reverse (de-liquidation), but fees and arbitrage losses are not reversed. It is both a lending collateral-management mechanism and a tradeable AMM.

For one band, the whitepaper gives the invariant (Eq. 6):
\[
\left(\frac{p_o^2}{p_\uparrow}A y_0+x\right)
\left(\frac{p_\uparrow}{p_o}(A-1)y_0+y\right)
=p_o A^2y_0^2,
\]
where:
- \(x\) is the borrowed-token balance in the band;
- \(y\) is the collateral balance;
- \(p_o\) is the oracle price;
- \(p_\uparrow\) is the upper band price;
- \(A\) is the band-width factor;
- \(y_0\) is a virtual collateral offset determined from the current band balances.

The band grid is:
\[
p_\uparrow(n)=p_{base}\left(\frac{A-1}{A}\right)^n,
\qquad
p_\downarrow(n)=p_{base}\left(\frac{A-1}{A}\right)^{n+1}.
\]
The source derives a quadratic for \(y_0\) (Eq. 7) and current marginal price relations (Eq. 8). These are derived state/price calculations, not separate invariant equations.

## 2. Structural comparison

The per-band invariant is a product of two affine virtual-balance terms. After scaling, it is constant product in virtual reserves, related to:
- Gyroscope 2-CLP's virtual-reserve constant-product invariant;
- Maverick V2's tick invariant in virtual reserves;
- Uniswap v3 concentrated-liquidity virtual reserves.

Thus the per-band invariant is not a new algebraic invariant family under a strict structural-form policy. The band geometry and oracle-dependent virtual offsets differ, but the core product structure is related.

The complete LLAMMA protocol mechanism is more distinctive:
- collateral is distributed over a user-selected band range (4–50 bands in documented deployments);
- each band transitions between collateral-only, mixed active-band and borrowed-token-only states;
- oracle price and internal AMM price create arbitrage incentives;
- price decline causes soft liquidation and price recovery can cause de-liquidation;
- repeated cycles can incur non-reversible fees/arbitrage losses and worsen borrower health;
- the AMM is coupled to lending controller, interest-rate accrual, oracle and liquidation logic.

This complete risk-management system may be a candidate if the benchmark's equation unit explicitly includes protocol state-transition systems, rather than only invariant formulas.

## 3. Source/version and adapter requirements

The documentation distinguishes crvUSD/LLAMMA and LlamaLend V2 implementations. They must not be silently conflated. A deterministic adapter must freeze:
- exact AMM/controller version and immutable source commit;
- borrowed/collateral token order and decimal normalization;
- oracle price \(p_o\), base price and interest-rate multiplier;
- band-width factor \(A\), band count and user band allocation;
- per-band \(x,y,y_0\) states and virtual-offset solution;
- fee/dynamic-fee, admin fee and rounding;
- arbitrage execution assumption and timing;
- soft-liquidation/de-liquidation transition, including irreversible fees/losses;
- hard-liquidation boundary and health-factor interaction.

A static per-band invariant adapter does not reproduce the full soft-liquidation mechanism. A full system adapter requires multiple bands, oracle and state transitions.

## 4. Decision

**Disposition:** retain LLAMMA as a strong protocol-risk and liquidation-system discovery lead. Do not count its per-band virtual-constant-product invariant as a new structural invariant beside Gyro/Maverick. Consider the complete multi-band soft-liquidation/de-liquidation state machine as a separate system-level candidate only if DeFi Risk explicitly admits protocol state-transition models and a deterministic system adapter is supported.

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, on-chain reads or protocol transactions were run. This is whitepaper/documentation-level discovery only.
