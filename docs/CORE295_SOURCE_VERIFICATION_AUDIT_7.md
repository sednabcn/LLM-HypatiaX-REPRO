# Core-295 source verification audit 7: Chainlink feed freshness is a consumer safety rule, not a universal equation

**Date:** 2026-11-11  
**Status:** source classification only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing DeFi Risk source lead RISK-CHAINLINK-FEED-FRESHNESS.

## 1. What the official source establishes

The registered source is Chainlink's official Data Feeds overview. Its current documentation states that push-based feed answers are updated when either:
- the off-chain reported value deviates beyond a feed-specific deviation threshold; or
- the configured heartbeat interval elapses.

The documentation says the heartbeat and deviation values are feed-specific and can differ by asset and blockchain. It directs consuming applications to inspect the timestamp from latestRoundData(), specifically updatedAt, and decide whether the answer is recent enough for the application's own acceptable time limit. It warns that a heartbeat update may be delayed slightly by congestion or network conditions.

The AggregatorV3Interface API reference confirms that latestRoundData() returns roundId, answer, startedAt, updatedAt and answeredInRound. It also explains that latestAnswer does not include a timestamp and is insufficient on its own for a freshness check.

## 2. Separate the oracle's update trigger from the consumer's validity guard

These are two different mechanisms:

1. **Provider/network update policy:** deviation threshold and heartbeat determine when the decentralized oracle network initiates an on-chain update. Their configured values are feed/network-specific. They are not one universal equation or fixed constant.
2. **Consumer-side freshness policy:** the consuming protocol reads updatedAt and compares it with an application-defined maximum age. A generic implementation may enforce a condition of the form
   updatedAt > 0 and block.timestamp - updatedAt <= maxAge,
   but maxAge is chosen by the consumer and depends on the asset, market, chain, risk tolerance and downstream use.

A consumer may also impose answer-domain checks (for example, rejecting nonpositive prices where a positive price is required), round-completeness checks, sequencer-uptime checks on L2, or deviation limits. Those are separate application policies and should not be attributed to Chainlink's universal interface unless the exact consumer contract and version are named.

## 3. Structural and catalogue decision

The registered lead describes oracle operations and consumer safety policy, not a standalone scientific/financial equation. The timestamp comparison is a simple implementation guard whose key threshold is application-defined; the heartbeat/deviation update logic is a feed configuration and network trigger, not a portable risk equation.

Accordingly:
- retain the source as protocol-risk and data-provenance context;
- do not count heartbeat, deviation threshold, updatedAt comparison and application-specific answer checks as four distinct equations;
- do not invent one universal heartbeat, deviation percentage or maxAge;
- if the DeFi Risk domain explicitly includes executable protocol safety predicates/state machines, define that class and sampling unit before deciding whether a version-pinned consumer guard is eligible.

**Register link:** RISK-CHAINLINK-FEED-FRESHNESS.

## 4. Decision

**Current disposition: source lead retained; not an equation candidate under the present equation-only interpretation.** Revisit only if the domain contract is broadened to include protocol safety predicates and a concrete consuming contract/version is selected. This audit does not alter the formal catalogue or accepted count.

## 5. Work not performed

No feed was queried, no on-chain data was read, and no API or protocol call was made. No contract was executed. No experiment, validator, solver, workflow or paid compute was run.
