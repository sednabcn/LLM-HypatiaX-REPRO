# Core-295 consolidated author-pool audit matrix 1

**Date:** 2026-11-11  
**Input:** user-supplied `author_pool.py` (299 statically inspected rows)  
**Status:** discovery-pool disposition index; not a benchmark, accepted catalogue, or experimental result.

No author-pool script was executed. No equations were generated, validated, fitted, solved, or benchmarked. No validator, workflow, experiment, paid compute, or live protocol/API call was run. This document consolidates the domain audits and points to their row-level reasoning; it does not replace those audits.

## 1. Domain-level disposition

| Domain | Raw author-pool rows | Target accepted models | Raw arithmetic gap | Accepted from author-pool audit | Current source-register records | Main disposition |
|---|---:|---:|---:|---:|---:|---|
| Chemistry | 54 | 59 | 5 | 0 | 33 | Do not import wholesale; source reconstruction, model-family clustering, units and regime constraints required |
| Biology | 59 | 59 | 0 | 0 | 34 | Raw count exactly matches target but is not an acceptance count; coupled systems and derived outputs materially reduce the apparent pool |
| Physics | 75 | 59 | 16 surplus | 0 | 43 | Broad textbook formula collection; many outputs, special cases, limits and linked models |
| DeFi AMM | 54 | 59 | 5 | 0 | 23 | Several rows are views of a few invariant families; protocol/version and state-transition contracts are missing |
| DeFi Risk | 57 | 59 | 2 | 0 | 33 | Generic finance identities, excluded Core-15 structures and protocol-unspecified heuristics dominate |
| **Total** | **299** | **295** | **0 net raw gap** | **0** | **166** | Raw row total is not evidence that 295 structurally distinct equations exist |

The arithmetic gap column is only (59-\text{raw rows}); it is not a feasibility estimate. Physics surplus cannot be transferred to another domain. A domain with fewer than 59 defensible models must expand its source universe rather than relax the structural rule or pad with variants.

The 169 source-register records are references/leads, not equations. The formal manifest remains **draft**, with **19 proposed**, **0 accepted**, and sampling frame **not frozen**. These 19 formal proposals are separate from the 299-row discovery pool.

## 2. Consolidated family and defect matrix

| Domain | Major families/overlaps identified | Source/provenance and model-validity blockers | Recommended next action |
|---|---|---|---|
| Chemistry | Integrated reaction laws with half-life summaries; Arrhenius/Eyring/van't Hoff/Clausius–Clapeyron activated/temperature families; acid/base/equilibrium inverses; Langmuir adsorption variants; Fick/Fourier/Ohm normalized transport operator; diffusion time/flux/PDE; solution activity and electrochemistry | Generic textbook placeholders; missing exact equation locations; convention-sensitive constants/log bases/activities; invalid or missing stoichiometry and physical ranges; dimensional defects; two-site occupancy and enzyme equilibrium issues | Select source-backed mechanisms first; reconstruct exact equations and conventions; identify parent model for derived outputs; define constrained joint samplers and regime-specific train/extrapolation domains |
| Biology | Michaelis–Menten/Lineweaver–Burk and hyperbolic saturation (Monod, Holling II, receptor occupancy, Emax); coupled Lotka–Volterra; SIR incidence vs full system; Beverton–Holt/Ricker; PK dosing and AUC summaries; gene-expression/toggle systems; Shannon/Simpson probabilities | Coupled systems split into pseudo-independent scalar rows; linearizations and steady states counted as independent; probability vectors not constrained to simplex; PK input/state contracts absent; physiological units and experimental context incomplete | Treat each closed coupled model as one declared unit; source and reconstruct full ODE/recurrence; define dosing/input protocol, constraints, units and observation model; decide if empirical model families are eligible |
| Physics | Newtonian gravity/orbits; constant-acceleration/projectile trajectory; circular motion; linear oscillator/circuit responses; Planck/Wien/Stefan/Rayleigh–Jeans; quantum/atomic; radioactive decay/activity; drag/terminal speed/Bernoulli; wave optics/acoustics; EM devices; thermodynamic processes; collisions and beam mechanics | Assistant-authored generic formulas with weak row-level sources; derived observables and limiting approximations; force-balance and special-solution overlaps; broad extrapolation defaults; SI/sign/boundary conditions not established | Use source register to reconstruct candidates; explicitly decide whether PDE special solutions and eigenproblems count; retain full model and boundary conditions; screen Core-15 and cross-domain normalized operators |
| DeFi AMM | Constant-product/Uniswap v2; Balancer weighted invariant; Uniswap v3 concentrated liquidity; Curve StableSwap/CryptoSwap; Bancor bonding curve; DODO PMM; discrete-bin Liquidity Book; YieldSpace power-sum; TWAP/oracle accounting | Swap outputs, spot prices, liquidity and depth often derived from one invariant; source labels are not citations; pool version, fixed-point arithmetic, fees, rounding, token order, decimals, oracle window and state transitions absent | Reconstruct one full invariant/state model per protocol version; use exact implementation commit; distinguish invariant from derived swap/price/LP observables; prioritize YieldSpace as a new time-dependent invariant lead and hold bin state machines pending full transitions |
| DeFi Risk | VaR and liquidation-price variants; portfolio covariance/volatility; EWMA/GARCH; health factor; utilization/rate/index accrual; APR/APY; Merton credit; funding/staking/reward models; oracle/bridge/governance/MEV risks | VaR, liquidation price and portfolio standard deviation overlap Core-15 exclusions; generic formulas lack venue/protocol definitions; invalid correlation bounds and unconstrained covariance; funding rates differ by venue; arbitrary quartic borrow curve not protocol-grounded | Freeze explicit Core-15 exclusion treatment; reconstruct Aave/Compound/perpetual formulas by exact version; enforce covariance/portfolio constraints; define return frequency, horizon, oracle, debt and accrual conventions |

## 3. Cross-domain blockers that affect the 295 count

1. **Same normalized operator, different mechanism:** the draft policy treats these as mechanism-diversity leads, not structurally distinct equations (E3). Examples include first-order exponential decay/relaxation and linear transport/Ohm/Fourier/Fick forms.
2. **Derived observables:** half-life, activity, AUC, price impact, spot price, LP balances, total radiation and similar outputs must not be counted as separate equations when derived from one governing model.
3. **Coupled systems:** do not split Lotka–Volterra, SIR, gene regulation, PK/PD or other coupled state systems into several nominally independent scalar records.
4. **Special/limiting cases:** Rayleigh–Jeans from Planck, constant-sum/product limits of YieldSpace, hydrostatic/Bernoulli specializations, and force-balance terminal speeds remain attached to their parent family unless the frozen policy explicitly defines a different model-level unit.
5. **Core-15 exclusions:** exact exclusions and their derived/reparameterized forms need a uniform rule before acceptance. Domain labels do not make an excluded structure new.
6. **Source family is not statistical independence:** different equations from one source, protocol, paper, dataset or generator do not automatically constitute independent calibration units.
7. **A valid sampler is part of the model contract:** unconstrained independent ranges are inadequate for correlated states, positive variables, probability simplices, covariance matrices, conservation laws, protocol fixed-point arithmetic or regime-limited physical laws.

## 4. Audit source documents

- Chemistry and Biology: [CORE295_AUTHOR_POOL_CHEM_BIO_AUDIT_1.md](CORE295_AUTHOR_POOL_CHEM_BIO_AUDIT_1.md) — 54 Chemistry + 59 Biology rows.
- Chemistry source refinements: [CORE295_CHEM_ADSORPTION_AND_MARCUS_AUDIT_1.md](CORE295_CHEM_ADSORPTION_AND_MARCUS_AUDIT_1.md) — Frumkin/Langmuir family and Marcus prefactor scope.
- Physics: [CORE295_AUTHOR_POOL_PHYSICS_AUDIT_1.md](CORE295_AUTHOR_POOL_PHYSICS_AUDIT_1.md) — 75 Physics rows.
- DeFi AMM and DeFi Risk: [CORE295_AUTHOR_POOL_DEFI_AUDIT_1.md](CORE295_AUTHOR_POOL_DEFI_AUDIT_1.md) — 54 AMM + 57 Risk rows.
- DeFi Risk protocol refinements: [CORE295_DEFI_RISK_PROTOCOL_MODELS_AUDIT_1.md](CORE295_DEFI_RISK_PROTOCOL_MODELS_AUDIT_1.md) — Aave V3 and Compound Comet models.
- Structural rules: [CORE295_STRUCTURAL_EQUIVALENCE_POLICY_DRAFT_1.md](CORE295_STRUCTURAL_EQUIVALENCE_POLICY_DRAFT_1.md) — provisional E0–E5 policy, not frozen.
- AMM source expansion: [CORE295_AMM_SOURCE_EXPANSION_AUDIT_1.md](CORE295_AMM_SOURCE_EXPANSION_AUDIT_1.md).

## 5. Gate before any candidate can count

A discovery row must not be promoted until it has:

1. Exact primary source or authoritative versioned protocol source, with equation/page/section or implementation file and commit.
2. Complete governing model, declared model class, state/inputs/outputs and derivation parent.
3. Dimensional and numerical consistency, sign/unit/token conventions, assumptions and validity domain.
4. Explicit pairwise E0–E5 review against Core-15 exclusions, proposed and accepted entries, and cross-domain families.
5. Defensible constrained train/extrapolation generator, seed policy and deterministic adapter.
6. Source-family ID and separately justified statistical-unit ID.
7. Independent human review and explicit acceptance decision.

**Current conclusion:** the uploaded 299-row pool is useful for discovery but supports **zero accepted author-pool equations** at this stage. This does not mean the 295 target has been disproven; it means the raw pool count cannot establish it. Continue source-led reconstruction without quota-driven promotion.
