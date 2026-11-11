# Core-295 source verification audit 10: Uniswap v2 arithmetic TWAP vs v3 geometric-mean-price oracle

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing DeFi Risk leads RISK-UNISWAP-V2-TWAP and RISK-UNISWAP-V3-TWAP. Official protocol documentation and the exact periphery commits registered in the source catalogue were checked.

## 1. Uniswap v2: arithmetic time-weighted mean of spot price

### 1.1 Mathematical definition

Uniswap v2 stores cumulative prices that integrate the reserve-ratio spot price over elapsed seconds. Given cumulative price observations (C(t_1)) and (C(t_2)), the average price over ([t_1,t_2]) is

[
operatorname{TWAP}_{v2}
=rac{C(t_2)-C(t_1)}{t_2-t_1}
=rac{1}{t_2-t_1}int_{t_1}^{t_2}p(t),dt.
]

The pair maintains two cumulative values, one for token1 per token0 and one for token0 per token1. This is necessary because the arithmetic mean of a price is not generally the reciprocal of the arithmetic mean of its reciprocal.

### 1.2 Pinned implementation details

The catalogue pins Uniswap/v2-periphery commit `ed24991304291297c3b4a52818d02f46a17aa9a2). Static source inspection confirms:
- `UniswapV2OracleLibrary.currentCumulativePrices` reads the pair's stored cumulative values and, if time has elapsed since the last pair update, adds a counterfactual reserve-ratio price multiplied by elapsed seconds;
- the timestamp is represented modulo (2^{32}), with subtraction wraparound intentional;
- `ExampleOracleSimple` computes each fixed-window average as cumulative-price delta divided by elapsed time;
- the result is represented as UQ112x112 fixed point;
- the example requires at least one configured period to have elapsed and stores separate token0/token1 averages.

The example uses a 24-hour period, but that is an example contract parameter, not a universal Uniswap v2 TWAP horizon.

## 2. Uniswap v3: geometric mean price via arithmetic mean tick

### 2.1 Mathematical definition

Uniswap v3 accumulates the active tick over time. For two observations separated by (Delta t), the arithmetic mean tick is

[
ar{	au}
=leftlfloor
rac{T(t_2)-T(t_1)}{Delta t}
ightfloor,
qquad
T(t)=int_0^t 	au(s),ds.
]

The tick-price relation is

[
p(	au)=1.0001^{	au}
]

for the protocol's token0/token1 orientation (the reciprocal applies for the opposite orientation, with token ordering and decimals handled explicitly). Therefore converting the arithmetic mean tick to price yields the time-weighted geometric mean of the instantaneous tick prices:

[
operatorname{GM}_{v3}
=exp!left(rac{1}{Delta t}int_{t_1}^{t_2}ln p(t),dtight)
=1.0001^{ar{	au}}.
]

The protocol documentation explicitly distinguishes this geometric mean price from the arithmetic mean price accumulated by v2.

### 2.2 Pinned implementation details

The catalogue pins Uniswap/v3-periphery commit `24ccf014fe7f81d74a14c1689d6fdf123f280e45`. Static inspection of `OracleLibrary.consult` confirms:
- it requests observations at `secondsAgo` and now;
- computes the delta of the signed tick cumulatives;
- divides by the requested interval to obtain an arithmetic mean tick;
- corrects Solidity's truncation-toward-zero behavior by decrementing a negative non-integral quotient, thereby rounding toward negative infinity;
- separately computes harmonic mean in-range liquidity from the seconds-per-liquidity accumulator.

The harmonic-mean-liquidity output is a different statistic from the price oracle and should not be bundled into the price equation as an additional price formula.

## 3. Structural comparison and family policy

These are not merely different parameter values of the same averaging equation:
- v2 estimates the arithmetic time average of the instantaneous reserve-ratio price;
- v3 estimates the geometric time average of the tick-implied price by averaging log-price ticks.

In general, arithmetic and geometric means differ. The distinction is substantive and can affect risk-sensitive downstream decisions. The two implementations are nevertheless members of one broader on-chain time-weighted oracle family and share common data/market dependencies; statistical independence is not established by their different estimands.

For Core-295:
- treat the v2 arithmetic-price TWAP as one equation-family candidate;
- treat the v3 geometric-price TWAP as a separate, structurally distinct statistic candidate only if the catalogue explicitly allows different averaging estimands within one oracle family;
- do not count cumulative accumulators, interval subtraction, fixed-point decoding, price conversion, inverse token orientation, or alternate observation windows as additional equations;
- do not count the v3 harmonic-mean-liquidity statistic as a price equation;
- specify pool/token ordering, price units, observation horizon, tick rounding, liquidity/observation availability and the exact protocol/periphery version;
- use the independent statistical unit at the underlying market/source-family level, not individual observation pairs from one pool trajectory.

## 4. Decision

**Current disposition: two credible, equation-level DeFi Risk leads; both held, not accepted.** The source and implementation checks establish a real mathematical distinction between arithmetic-price TWAP and geometric-price TWAP. Their treatment as two distinct entries remains conditional on the predeclared structural-family and independence policy.

## 5. Work not performed

No pool was queried, no on-chain data or oracle observation was read, and no transaction or protocol call was made. No experiment, solver, validator, workflow or paid compute was run. No formal catalogue entry or source status was changed.
