# Core-295 candidate discovery batch 19: DeFi Risk oracle integrity and freshness

**Status:** official protocol documentation and implementation tracing only. No equation is accepted or counted toward the 59 DeFi Risk target.

## 1. Uniswap v2 cumulative-price arithmetic TWAP

**Official sources:** [Uniswap v2 Oracles](https://developers.uniswap.org/docs/protocols/v2/concepts/oracles) and [Uniswap v2 Core whitepaper](https://uniswap.org/whitepaper.pdf).

A pair contract accumulates the price ratio observed at the end of each block, weighted by the elapsed time since the previous update. For a price process \(P(t)\), the cumulative price is conceptually:

\[
C(t)=\int_0^t P(\tau)\,d\tau.
\]

The arithmetic time-weighted average over \([t_1,t_2]\) is:

\[
P_{TWAP}=\frac{C(t_2)-C(t_1)}{t_2-t_1}.
\]

The on-chain implementation stores fixed-point cumulative values (UQ112x112) and uses a modulo-\(2^{32}\) timestamp delta. Consumers must store or otherwise obtain the start cumulative observation; the pair does not maintain arbitrary historical snapshots.

**Risk boundary:** this is a time-averaged price oracle, not the pool's instantaneous spot price. Longer averaging windows generally raise manipulation cost but increase lag. Do not count the integral definition, cumulative-sum implementation, arithmetic mean, fixed-point decoding and token-direction reciprocal as separate equation families.

## 2. Uniswap v3 tick-cumulative geometric TWAP and harmonic mean liquidity

**Official source:** [Uniswap v3 Price Oracles](https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles). **Implementation:** [OracleLibrary.sol](https://github.com/Uniswap/v3-periphery/blob/main/contracts/libraries/OracleLibrary.sol), captured file blob SHA `ddb82be610e5694581de1553fe86f4ca3da82e55`.

The pool accumulates the active tick per second. Over an interval of length \(\Delta t\):

\[
\bar{tick}=\frac{tickCumulative(t_2)-tickCumulative(t_1)}{\Delta t},
\qquad
P_{TWAP}=1.0001^{\bar{tick}}.
\]

Because tick is logarithmic in price, this is a geometric mean price, not the arithmetic price TWAP used by Uniswap v2. The implementation rounds the mean tick toward negative infinity for negative non-integer results.

The seconds-per-liquidity accumulator gives the harmonic mean of active liquidity:

\[
L_H=\frac{\Delta t\,2^{128}}
{\Delta(secondsPerLiquidityX128)}.
\]

The contract uses fixed-point scaling and overflow-safe arithmetic; the exact Solidity expression in OracleLibrary shifts the cumulative delta by 32 and multiplies the elapsed time by the maximum uint160 value.

**Risk boundary:** the geometric price TWAP and harmonic mean liquidity are linked outputs of the same observation system, but they measure different quantities. The harmonic mean liquidity can help characterize the liquidity available over the window; it is not a direct guarantee of manipulation cost. Record tick rounding, observation cardinality, interpolation, timestamp range and active-liquidity semantics.

## 3. Chainlink feed freshness and update triggers

**Official source:** [Chainlink Data Feed overview](https://docs.chain.link/data-feeds/overview) and [historical data guidance](https://docs.chain.link/data-feeds/price-feeds/historical-data).

Chainlink feeds update when an off-chain deviation threshold is exceeded or a heartbeat interval elapses. The provider's update trigger is distinct from a consumer's freshness requirement. A consuming protocol should check the reported update timestamp and apply its own maximum-age condition, conceptually:

\[
now-updatedAt\leq maxAge.
\]

The consumer may also apply acceptable price bounds, stale-feed fallback, pause or alternate-oracle behavior. Heartbeat and deviation settings vary by feed and network; the documentation explicitly warns that consumers must not assume all feeds share the same values.

**Risk boundary:** the freshness inequality is a consumer-side safety policy, not a universal Chainlink feed equation. Do not promote a specific maxAge or deviation percentage as a general formula. Pin the feed address, network, decimals, heartbeat, deviation threshold, aggregator/proxy version and fallback logic.

## Cross-family overlap and acceptance controls

- Uniswap v2 arithmetic TWAP and Uniswap v3 geometric TWAP are distinct averaging constructions; do not conflate them or call both an arithmetic mean.
- The v3 harmonic mean liquidity accumulator is a related observation statistic, not an independent oracle price.
- Chainlink heartbeat/deviation triggers and consumer-side stale-answer checks are separate protocol and integration layers. They are not a single universal threshold.
- TWAPs are vulnerable to manipulation depending on liquidity, window length, market depth and arbitrage. A formula alone does not quantify attack cost.
- Do not count spot price, cumulative price, average price, reciprocal quote, fixed-point conversion, tick-to-price conversion and rounding variants as independent risk equations.
- These oracle systems belong to a common DeFi price-oracle risk cluster, even though their mathematical accumulators differ. Protocol-level samples are not automatically independent statistical units.

## Acceptance requirements

For every oracle candidate, specify pool/feed version, token ordering, quote units, observation window, timestamp arithmetic, fixed-point scale, interpolation, rounding, minimum history, active liquidity, feed decimals, heartbeat/deviation thresholds, maximum age and fallback behavior. Include a deterministic attack/manipulation-risk scenario only if it can be evaluated without live protocol calls.

All records remain candidates. No DeFi Risk entry is accepted; no live oracle query or workflow has been run.
