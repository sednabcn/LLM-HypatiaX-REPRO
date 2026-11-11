# Core-295 source verification audit 43: Swaap V2 RFQ market-making and on-chain safeguards

**Date:** 2026-11-11  
**Status:** classification of existing source-register lead AMM-SWAAP-V2-WP; no equation is added to the formal catalogue or counted toward 295.

## 1. Whitepaper scope and architecture

Swaap Labs, *Swaap v2: Optimal liquidity infrastructure*, 1 June 2023, describes Swaap V2 as a non-custodial request-for-quote (RFQ) market-making infrastructure. The whitepaper explicitly defines RFQ: traders receive signed quotes in response to trading requests and later settle by accepting those quotes.

The architecture separates:
- on-chain inventory/vault and settlement;
- off-chain quote generation by a whitelisted quote provider;
- on-chain safeguards that validate or reject the quote before execution.

The whitepaper says the inventory vault is a plain fork of Balancer V2's Vault, but the quotation model is off-chain. The objective is a stochastic-control/mean-variance optimization of LP PnL relative to a benchmark, with bid/ask markups as controls. The v2 paper does not define a new on-chain constant-function invariant or a self-contained deterministic price curve.

## 2. On-chain safeguard predicates

The whitepaper gives three principal settlement checks:

### Max-drawdown circuit breaker

A proposed trade is rejected if the pool's post-trade value relative to HODL over the selected epoch falls below a threshold:
\[
\frac{\sum_i r_i^t o_i^t}
{\sum_i [r_i]_{e_\phi(t)}o_i^t}>1-y.
\]
Here \(r_i^t\) are post-trade reserves per pool token, \(o_i^t\) oracle prices, \([r_i]_{e_\phi(t)}\) the reserves at the epoch start, and \(y\) the maximum tolerated drawdown.

### Last-look price guard

A trade is rejected if the quote price for token \(i\) is too far below the oracle price:
\[
\frac{q_i^t}{o_i^t}>1-d,
\]
where \(q_i^t\) is the signed quote price, \(o_i^t\) the oracle price and \(d\) the allowed deviation. The direction is important: the guard is designed to prevent underpricing relative to the oracle.

### Max-imbalance guard

The whitepaper gives a reserve-composition constraint comparing the post-trade pool's oracle-valued asset weights to the initial/epoch reference weights. It is an on-chain settlement predicate with an epoch and reserve-history dependency, not a universal market-making invariant.

These checks are protocol-specific safeguards. They depend on the quote, oracle, epoch mapping, pool-token reserve accounting and immutable threshold parameters. They are not independent equations of the pool's price curve.

## 3. Domain and structural classification

Swaap V2 is related to automated market making because it manages LP inventory and uses a Balancer-derived vault, but its distinguishing v2 quotation mechanism is RFQ rather than an on-chain constant-function AMM. Its stochastic-control quote objective is an optimization problem, not a closed-form invariant equation.

Under a strict DeFi AMM domain limited to on-chain invariant-based pools, Swaap V2 should be retained as architecture context, not as a new AMM equation. Under a broader DeFi market-making/risk domain, the drawdown, last-look and imbalance safeguards may be modeled as a single version-pinned settlement-policy system. They should not be counted as three independent universal equations.

## 4. Decision

**Disposition:** source and architecture verified. Keep AMM-SWAAP-V2-WP as RFQ market-making and protocol-safeguard context. Do not count it as a new constant-function AMM invariant. Consider the complete on-chain safeguard/settlement system only if the DeFi Risk domain explicitly admits protocol-specific executable predicates and the exact on-chain implementation is pinned.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, live API calls, quote requests, pool reads or transactions were run. This is whitepaper-level source review only.
