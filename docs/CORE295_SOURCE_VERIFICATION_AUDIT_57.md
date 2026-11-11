# Core-295 source verification audit 57: Maker MIP45 provenance, supersession and auction invariants

**Date:** 2026-11-11  
**Status:** primary-source provenance clarification for RISK-MAKER-MIP45-LIQ2 and Audit 48. No equation is added to the formal catalogue or counted toward 295.

## 1. Primary proposal and lifecycle status

Maker Improvement Proposal MIP45, *Liquidations 2.0 – Liquidation System Redesign*, was proposed 3 February 2021 and ratified in March 2021. The current MIPs portal marks it **obsolete**, with the editor commentary that it was made obsolete by MIP102c2-SP1.

The MIP0 Endgame framework states that MIPs outside the designated Endgame MIP set lose active status and are considered obsolete. This is a governance-document status change; it does not by itself establish that already deployed Dog/Clipper contracts ceased operating or that all historical Liquidations 2.0 mechanics were removed. MIP45 remains useful as the primary historical design specification, but it must not be represented as a currently active governance mandate.

## 2. Primary design details

MIP45 replaces the earlier English-style collateral auction with a Dutch-style auction:
- Dog.bark confiscates the undercollateralized Vault and transfers all its debt to protocol bad-debt accounting;
- the corresponding Clipper auction offers collateral for DAI at a price derived from the initial OSM price and a configurable buffer;
- bidders may purchase partial collateral lots at the current price, with instant settlement;
- the auction's DAI target includes debt, accrued stability fees and liquidation penalty;
- global Hole/Dirt and per-collateral ilk.hole/ilk.dirt capacity controls constrain active-auction exposure;
- keepers receive configurable flat and percentage incentives;
- a four-stage circuit breaker can disable new auctions, resets, and finally all takes.

Unlike the earlier system's per-liquidation debt slice (dunk), MIP45's Dog.bark transfers the full Vault debt into the liquidation system; partial collateral purchases occur later through Clipper.take.

## 3. Auction price functions and reset semantics

MIP45c13 specifies an interchangeable Abacus price function with the initial auction price and elapsed time as inputs. The proposal lists:
- LinearDecrease with tau;
- StairstepExponentialDecrease with cut and step;
- ExponentialDecrease with per-second cut.

These are alternatives, not simultaneous equations in one auction. The stair-step and continuous exponential functions coincide when step is one second. The price may increase after a reset or governance parameter/calculator change, even though each configured price calculator is decreasing in elapsed time. Therefore a benchmark adapter must distinguish within-auction decay from between-reset price changes.

## 4. MIP45 accounting invariants

The proposal records intended Dog/Clipper invariants:
\[
\sum_{\text{ilks}} ilk.dirt=Dog.Dirt,
\]
\[
\sum_{\text{active auctions}} tab=Dog.Dirt,
\qquad
\sum_{\text{active auctions of ilk}} tab=ilk.dirt.
\]
It also states:
\[
\sum_{\text{active auction ids}} lot\le Vat.gem(Clipper).
\]
The inequality is only a pseudo-invariant: unauthorized or governance-created Clipper.kick calls that fail to transfer collateral can violate the accounting premise. MIP45 explicitly says these invariants had not yet been formally proven and should be treated as intended behavior.

These are cross-contract accounting consistency properties, not independent economic equations. The Dog/Clipper state machine, price calculators, capacity accumulators, reset rules and circuit breaker form one liquidation-auction system family.

## 5. Relationship to Audit 48

Audit 48 pins a later source snapshot in the Sky ecosystem repository, branch liq-2.0, and classifies the same Dog/Clipper/Abacus architecture. That audit's commit pin is useful for reproducibility of the inspected source, but it does not establish the currently deployed implementation or override MIP45's obsolete governance status. The exact deployment and any post-MIP45 changes must be identified before a production-faithful adapter is defined.

## 6. Decision

**Disposition:** retain MIP45 as a historical primary design specification for the Dutch-auction liquidation system; mark its governance proposal status obsolete. Keep its formulas and accounting invariants grouped with the pinned Dog/Clipper/Abacus implementation in Audit 48. Do not count the three Abacus calculators, auction invariants, Hole/Dirt accounting, or reset/settlement operations as separate equation candidates.

No formal source-register or equation-catalogue record was changed. The source register remains 129 records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No live deployment, on-chain state, auction or governance vote was queried. No experiments, validators, solvers, workflows, paid compute, API calls or transactions were run. This is proposal and static-source review only.
