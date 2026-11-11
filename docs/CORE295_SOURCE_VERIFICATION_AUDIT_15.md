# Core-295 source verification audit 15: Liquity V1 Stability Pool product-sum accounting

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing DeFi Risk lead RISK-LIQUITY-STABILITY-POOL. The Liquity V1 product-sum derivation paper, V1 protocol documentation and the current repository source snapshot were checked. No chain state or protocol was queried.

## 1. Primary derivation and mechanism

Richard Pardoe, *Scalable Reward Distribution with Compounding Stakes*, v1.0, December 2020, derives a pull-based accounting method for Liquity V1's Stability Pool. Deposits in LUSD are reduced pro rata as liquidated debt is offset; in return, depositors receive a pro-rata share of collateral. Rather than updating every depositor after every liquidation, the system tracks a global product (P) and sum (S), then calculates each depositor's compounded deposit and collateral gain from their initial deposit and snapshots.

This is an accounting algorithm for a stateful risk-sharing mechanism, not a single scalar risk metric. Its defining object is the coupled product-sum update and the depositor snapshot adapter.

## 2. Mathematical derivation

Let:
- (Q_i) be the debt offset by the Stability Pool at liquidation (i);
- (E_i) be collateral sent to the Stability Pool at liquidation (i);
- (D_{i-1}) be total deposits immediately before liquidation (i);
- (d_0) be a depositor's initial deposit.

The pro-rata depletion factor at liquidation (i) is
[
p_i=1-rac{Q_i}{D_{i-1}}.
]
The cumulative product is
[
P_n=prod_{i=1}^{n}p_i
=prod_{i=1}^{n}left(1-rac{Q_i}{D_{i-1}}ight),
]
so the compounded deposit is
[
d_n=d_0P_n.
]

Define the running collateral-gain sum
[
S_n=sum_{k=1}^{n}
left(rac{E_k}{D_{k-1}}ight)P_{k-1},
qquad P_0=1.
]
Then the depositor's cumulative collateral gain is
[
e_n=d_0S_n.
]

For a depositor entering after earlier liquidations, with product and sum snapshots (P_t,S_t), the paper derives
[
d_n=d_trac{P_n}{P_t},
qquad
e_n=d_trac{S_n-S_t}{P_t}.
]
These are the core product-sum relations. The individual liquidation loss, product update, sum update, compounded-deposit query and gain query are not separate independent equations.

## 3. Implementation comparison and important differences

The fetched `liquity/dev` V1 `packages/contracts/contracts/StabilityPool.sol` source snapshot has blob SHA `160433359c03930109b749584cad42b30a53de13`. It confirms:
- global product (P) and per-scale sum (S);
- depositor snapshots of (P), (S) and scale;
- collateral gain from the difference in (S)-snapshots divided by the depositor's (P)-snapshot;
- compounded deposit from initial deposit multiplied by current (P/P_{mathrm{snapshot}});
- product update from the per-unit LUSD loss and sum update from the per-unit collateral gain;
- feedback error correction for integer division.

The deployed implementation is not just the real-valued paper formula:
- arithmetic uses fixed-point integer scaling;
- the implementation uses a scale factor of (10^9) and handles one scale crossing explicitly in deposit and gain calculations;
- the implementation carries rounding-error correction terms for LUSD loss and collateral gain;
- the source also tracks LQTY issuance through an additional sum (G), which is a reward-distribution extension and should not be counted as another independent Stability Pool risk equation.

The paper discusses pool-emptying with an epoch reset. The fetched V1 contract instead asserts that the debt offset is strictly less than total Stability Pool deposits and maintains a minimum pool deposit; its current implementation does not use the paper's general epoch-reset scheme. Do not import the paper's epoch mechanism into a benchmark adapter unless the exact selected implementation/version requires it.

The source register currently identifies the official V1 documentation but does not pin an immutable commit for the Solidity implementation. The fetched blob SHA identifies the inspected file content, not a reproducible repository commit.

## 4. Structural and sampling classification

The product-sum construction is mathematically more than a proportional allocation identity: it tracks a compounding, decreasing stake and its cumulative collateral gain with constant-size global state. It is a plausible system-level DeFi Risk candidate if the benchmark's domain contract includes protocol risk-sharing and liquidation-accounting mechanisms.

However:
- (P), (S), compounded deposits and collateral gains are one coupled algorithm, not four entries;
- the per-liquidation pro-rata loss and collateral distribution are the economic mechanism underlying the algorithm;
- LQTY reward sum (G), front-end kickback logic, user snapshots, scale bookkeeping and rounding correction are implementation features or reward extensions, not additional independent equations;
- this is a protocol accounting mechanism, not a general-purpose credit-risk equation;
- Liquity V1 and V2 Stability Pool mechanisms must not be conflated.

A benchmark adapter must freeze the exact Liquity V1 version, token/collateral units, eligible liquidation offset, total-deposit convention, deposit timing, snapshot semantics, scale handling, error-correction rules and output target. A scalar adapter that samples independent (Q_i,E_i,D_i) tuples without enforcing the actual state transitions would not reproduce the system.

**Disposition:** credible complete-system risk-sharing/accounting lead; hold pending immutable implementation pin, Recovery Mode/domain-scope contract and a deterministic stateful system adapter. Do not count the paper's component identities or code bookkeeping as separate candidates.

## 5. Catalogue and experiment status

No catalogue record, source status, proposed count or accepted count was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, live API calls, oracle queries, on-chain reads or protocol transactions were run. This is source and static implementation review only.
