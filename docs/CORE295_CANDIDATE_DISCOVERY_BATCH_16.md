# Core-295 candidate discovery batch 16: Solidly, Swaap and Carbon AMM mechanisms

**Status:** protocol-source tracing only. No equation is accepted or counted toward the 59 DeFi AMM target.

## 1. Solidly V2 stable-pool invariant

**Official source:** [Solidly V2 Swaps](https://docs.solidly.com/dex-basics/swaps.html).

Solidly documents two pool curves:
- Volatile pairs: \(xy=k\), the constant-product invariant (Core-15 exclusion).
- Stable pairs: \(x^3y+xy^3=k\), equivalently \(xy(x^2+y^2)=k\).

The stable curve is designed for highly correlated assets and has lower slippage near balanced reserves than the volatile constant-product curve. It is a polynomial invariant distinct from Curve StableSwap's amplified sum/product blend.

**Boundary:** count the stable polynomial only as one candidate family, subject to exact implementation/version review. Do not count the volatile curve, stable-pool price derivative, swap-output rearrangements or the two equivalent polynomial notations as separate candidates. Solidly V3 is a concentrated-liquidity fork of the Uniswap v3 design and does not create a new invariant family merely by range restriction.

## 2. Swaap v2: RfQ market making and settlement safeguards

**Primary source:** Swaap Labs, *Swaap v2: Optimal liquidity infrastructure*, June 1, 2023, [whitepaper PDF](https://swaap.xyz/v2-whitepaper.pdf).

Swaap v2 is an off-chain request-for-quote market-making architecture with on-chain inventory and settlement safeguards, rather than a conventional invariant-based AMM. Section 2.2 formulates quote-provider markup selection as a stochastic optimization:

\[
\delta^*=
\sup_{(\delta_{buy},\delta_{sell})\in\mathcal A}
\mathbb E[PnL-B],
\]

where \(\mathcal A\) is the admissible markup space, \(PnL\) is LP profit/loss and \(B\) is the benchmark process.

Section 2.3 adds deterministic settlement checks:
- **Maximum drawdown:** the post-trade pool value relative to HODL at the current epoch must exceed \(1-y\), with the whitepaper's value ratio computed from per-pool-token reserves and oracle prices.
- **Last look:** a quote price for token \(i\) must remain within the configured deviation \(d\) of its on-chain oracle price; the paper prints the lower-bound check \(q_i^t/o_i^t>1-d\).
- **Maximum imbalance:** the purchased-token reserve ratio is constrained against fee-augmented epoch-start reserves and oracle values.

**Boundary:** the stochastic optimization objective is not a deterministic closed-form scalar equation unless the benchmark process, stochastic state, admissible strategy space and objective are specified. The drawdown, last-look and imbalance checks are protocol safeguards, not independent AMM invariant families. Keep them together as one RfQ market-making/settlement source family. The whitepaper describes an architecture with off-chain quote providers; do not imply the on-chain contracts independently calculate the optimal quote.

## 3. Carbon DeFi: asymmetric adjustable bonding curves

**Protocol source:** [Introducing Carbon](https://medium.com/carbondefi/introducing-carbon-1f41aebf634b).

Carbon describes one-sided buy or sell curves whose parameters include a starting price, ending price and capacity. A buy curve and a sell curve can be linked into a strategy backed by shared collateral. The user can adjust curve parameters without withdrawing and recreating liquidity.

**Boundary:** the overview does not provide the complete mathematical price/quantity function or the contract's exact transition rule. Keep Carbon as a protocol source lead only. Before promoting an equation, recover the official whitepaper, exact curve formula, rounding, fee convention, one-sided inventory semantics and the deployed contract version. Do not infer a linear or exponential curve from the start/end/capacity parameterization alone.

## Cross-family overlap and acceptance controls

- Solidly's stable polynomial \(xy(x^2+y^2)=k\) is distinct from pure constant product and from Curve StableSwap. The volatile \(xy=k\) pool remains excluded.
- Solidly V3's Uniswap-v3-derived concentrated liquidity is a range restriction of a constant-product curve, not a new invariant.
- Swaap's RfQ quotation objective and on-chain safeguards form a distinct market-making architecture, but the objective is stochastic and the settlement inequalities are risk constraints. Include them only if the predeclared DeFi AMM domain includes RfQ systems.
- Carbon's adjustable buy/sell orders are an algorithmic market-making lead, not an equation candidate until exact curve mathematics and state transitions are sourced.
- Protocol names, stable/volatile labels, parameter settings, fee schedules and equivalent rearrangements do not create structurally distinct equations.

All source records remain candidates. No DeFi AMM entry is accepted; no experiment, live quote request or workflow has been run.
