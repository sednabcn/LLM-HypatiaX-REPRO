# Core-295 design record (Option 2)

**Status:** selected design; catalogue, implementation, and validation are not complete.  
**Decision date:** 2026-11-11  
**Branch:** `promotion/rerun-code-review`

## 1. Decision

Core-295 is specified as **295 structurally distinct equations: 59 per domain** across the five Core-15 domains:

1. Chemistry
2. Biology
3. Physics
4. DeFi AMM
5. DeFi Risk

This is **Option 2**, selected by the user. It is not 295 coefficient variations of Core-15 and not 20 full Core-15 replications. Twenty complete Core-15 datasets would contain 300 equations. The target remains 295 unless explicitly changed.

Structural distinctness does not, by itself, prove statistical independence. The source universe, source-family relationships, sampling method, and independent statistical unit must be declared before the 59-per-domain sample can support a calibration-risk claim.

## 2. Preserve Core-15 architecture and scientific settings

The design changes the benchmark population, not the experimental machinery. Unless explicitly approved otherwise, Core-295 preserves the corresponding Core-15 implementations and settings:

- Model/hybrid architecture, method definitions, routing and fallback behaviour.
- Data-generation sample counts, noise, train/test handling, and extrapolation protocol.
- Optimizer/training settings, PySR search configuration, seeds, retries and timeouts.
- Metrics, canonical R-squared scoring, result semantics, and stage order.

The current Core-15 ablation implementation is `hypatiax/experiments/benchmarks/exp1_ablation.py`; it defines the 15-equation catalogue, data generators, and ablation arms. The five-system implementation is `hypatiax/experiments/benchmarks/exp1_five_system.py`; it reuses the Core-15 catalogue and generators but compares five different methods. They are distinct experiments and must not be conflated.

The existing five-system NN method is the current `ImprovedNNMethod` wrapper. Do not silently substitute a new network for Core-295. Preserve the current code for comparability, while disclosing known differences between implementation and manuscript descriptions.

## 3. Catalogue specification

The source-discovery policy and initial reference register are maintained in [CORE295_SOURCE_CATALOGUE_PLAN.md](CORE295_SOURCE_CATALOGUE_PLAN.md), and the machine-readable draft is `config/core295_catalogue.json`. The draft pins the 15 Core-15 names as exclusions; it deliberately contains no accepted Core-295 entries yet.

Every equation record must carry:

- Stable unique equation ID, domain, and scientific subdomain.
- Canonical symbolic expression and normalized form.
- Variable meanings and units; parameter meanings, valid ranges, and interpretation.
- Source citation or authoritative provenance; source-family/derivation ID.
- Validity assumptions, domain of applicability, and boundary constraints.
- Input sampling ranges, expected output properties, and extrapolation ranges.
- Generator version, seed if applicable, timestamp, and formula/data hashes.
- Validation status, reviewer decision, and caveats.

An equation does not count as structurally distinct merely because a coefficient, constant, unit scale, or variable name changes. Apply symbolic normalization, exact duplicate checks, algebraic-equivalence checks where feasible, and explicit flags for cosmetic rescaling/renaming. Record limitations of equivalence detection and require scientific review for borderline cases.

Validate dimensional consistency where applicable, physical/financial constraints, singularities, signs, valid operating ranges, finite outputs, and numerical stability. Keep source-family clustering even when formulas are structurally distinct. Do not claim 59 independent observations merely because there are 59 IDs or 59 different strings.

### Sampling-frame decisions still required

Option 2 fixes the target type and count, but the following must be frozen before catalogue generation:

- Authoritative source universe and inclusion/exclusion rules per domain.
- Definition of source family and dependency/cluster rules.
- Random, stratified, or curated sampling method and how the 59-per-domain quota is selected without cherry-picking.
- Independent statistical unit and whether each domain is a separate target population.
- Handling of insufficiently sourced or invalid equations.

If a domain cannot supply 59 defensibly distinct equations, do not pad it with cosmetic variants. Expand the declared source universe or request an explicit design revision.

## 4. Data generation and leakage controls

Preserve Core-15 data-generation/evaluation conventions unless a deviation is versioned and justified. For each equation, record generator version, seed, parameter values, input ranges, formula hash, and data hashes. Keep training, ordinary test, and extrapolation data separate. Do not use held-out or extrapolation outcomes to select equations, tune routing thresholds, revise the generator, or replace failed equations. Record failures and retries explicitly. Freeze and hash the catalogue/data manifest before evaluation.

Core-295 IDs must not collide with Core-15 IDs. Record scientifically related source families rather than hiding dependencies.

An offline manifest validator (`scripts/validate_core295_catalogue.py`) checks entry fields, source references, duplicate IDs/fingerprints, Core-15 exclusions, and readiness quotas. The offline shard planner (`hypatiax/experiments/benchmarks/core295_catalogue.py`) assigns accepted equations deterministically and verifies exact-once coverage; its default 100-shard plan is a dry-run only. Tests are wired into the read-only R2 policy CI workflow. These checks do not establish scientific validity or independence.

## 5. CI shards and per-run workers

### Sharding changes; model workers do not

Core-15 `exp1_ablation` currently uses five shards, one per domain, with three equations per domain. A five-shard Core-295 plan would put 59 equations on each shard—about 19.7 times the Core-15 equation count per shard—and is unlikely to fit the existing 330-minute worker timeout.

A **provisional planning target is 100 GitHub Actions shards** for 295 equations (about 2–3 equations per shard). This is a workload estimate, not a runtime guarantee. Matrix jobs may queue; 100 shards does not mean 100 concurrent jobs. Final count must be justified against observed per-equation runtimes, Actions quotas, artifact overhead, and aggregation.

The task planner must allocate deterministically and balance domains, with stable shard IDs and exact-once task coverage. A contiguous block split over a domain-grouped catalogue may yield poor domain balance; do not use it without verifying allocation.

Keep unchanged:
- Model architecture and per-equation method settings.
- Per-job PySR population and Julia thread count.
- Internal worker/parallelism settings and per-equation budgets.

Inspected current workflow settings include `JULIA_NUM_THREADS=4`, `PYSR_POPULATIONS=30`, a 330-minute worker timeout, and `JOB_DEADLINE=19800` seconds. The workflow exposes `n_shards`; no separate `n_worker` dispatch input was found in the inspected workflow/Core-15 runner. Thus, `n_worker` remains unchanged/not separately configurable unless a concrete setting is identified. Shard count is scheduling, not a model hyperparameter, and must be recorded in provenance.

## 6. Core-295 pipeline stage mapping

The Core-15 stage sequence in `run_all.sh` is explicit:

1. `exp1_ablation` — execute the three ablation arms for each equation.
2. `exp1_ablation_aggregate` — merge shard checkpoints, enforce equation/arm completeness, and produce the aggregate ablation analysis.
3. `exp1_five` — run the separate five-system comparison through `exp1_five_system.py`.

The Core-295 names map to those three distinct responsibilities, in order:

| Core-295 stage | Core-15 counterpart | Responsibility |
|---|---|---|
| `exp295_ablation` | `exp1_ablation` | Per-equation ablation execution |
| `exp295` | `exp1_ablation_aggregate` | Shard merge, completeness checks, aggregate ablation analysis |
| `exp295b` | `exp1_five` | Separate five-system comparison |

This resolves the earlier mapping ambiguity: `exp295` is the aggregate stage, not a second independent five-system experiment. `exp295b` is the five-system comparison. These mappings preserve the Core-15 sequence and do not conflate ablation execution, aggregation, and five-system benchmarking.

**Implementation status:** the mapping is now documented, but none of the three Core-295 stages is implemented or dispatchable yet. The current `run_all.sh` step registry and `.github/workflows/ci_runner_repro.yml` dispatch options contain the Core-15 IDs, not these Core-295 IDs. Do not dispatch a run until the Core-295 catalogue, stage implementations, sharding, result namespaces, and completeness contracts are ready.

Each stage needs isolated result/checkpoint namespaces, stable equation task IDs, workflow metadata, Julia requirement, seed policy, shard allocation, artifact paths, aggregation, and completeness checks. The aggregate stage must consume only artifacts from the same declared run and must reject missing, duplicated, or unexpected equation IDs. Final completeness must report 295/295 overall and 59/59 per domain.

Add dry-run/offline checks for task planning, sharding, checkpoint identity, aggregation, and result completeness. Preserve all existing Core-15 stage behavior and settings. Do not dispatch the workflow as part of implementation.

## 7. Approved tau-calibration protocol

| Parameter | Approved value |
|---|---:|
| Absolute LLM edge (R^2) floor | 0.99 |
| Relative margin (gamma) | 0.00 |
| Maximum tolerated bad-routing risk (arepsilon) | 0.05 |
| Family-wise error rate (delta) | 0.05 |
| One-sided confidence | 95% |
| Minimum per-category sample with zero failures | 59 independent equations |

The (R^2\geq0.99) floor aligns with the manuscript's primary recovery criterion. (R^2\geq0.999999) remains a separate near-exact criterion; (R^2<-10) is a separate catastrophic threshold. The choices (gamma=0), (arepsilon=0.05), (delta=0.05), and 95% confidence are protocol decisions, not manuscript-specified values.

### Fixed-sequence selection

Predeclare a finite candidate-(\tau) grid from strictest to laxest (ascending (\tau)). Test each candidate in order using the exact one-sided binomial test:

\[
H_0:p_{\mathrm{bad}}(\tau)\geq\varepsilon
\qquad\text{versus}\qquad
H_1:p_{\mathrm{bad}}(\tau)<\varepsilon.
\]

Test each candidate at the full predeclared (delta=0.05); continue only while certified and stop at the first failure. Select the last passing candidate. If the strictest fails, no threshold is certified and that category remains on ensemble fallback. This controls family-wise error at (delta) for a finite, predeclared sequence when tests and sampling assumptions are valid.

For zero observed failures:

\[
n_{\min}=\left\lceil\frac{\log(\delta)}{\log(1-\varepsilon)}\right\rceil=59.
\]

This is 59 independent equation-level units per category—not seeds, noise replicates, or rows from one equation. With failures, use the exact one-sided binomial upper bound; 59 is not a general guarantee for nonzero failures. The guarantee is per category; a simultaneous five-domain claim needs multiplicity control or a predeclared joint design.

### Core-295 and calibration

A structurally distinct catalogue is an improvement over parameter variants but does not automatically establish independence. The 59-per-domain risk bound requires a justified independent Bernoulli equation-level sampling design from a declared target population. Related equations from one source family may be dependent and require clustering or more conservative analysis.

The calibration set must be predeclared, training-only, and disjoint from Core-15 evaluation. Freeze the candidate (\tau) grid, category definitions, bad-route definition, evaluator version, and independence argument before observing outcomes. Do not use Core-15 outcomes, held-out labels/scores, or extrapolation results to select/revise (\tau). Equality (Delta\leq\tau) permits pure LLM routing only if all other gates pass. If evidence is insufficient, retain ensemble fallback and leave (\tau) unset.

## 8. Manifest/readiness status

`config/tau_calibration_manifest.json` remains a draft. It contains approved constants and Core-15 exclusion intent, but the calibration equation list and candidate-(\tau) grid are empty and category, independence, and edge-definition fields remain unset. Do not mark it ready or invent a numeric (\tau). The validator checks structure, leakage, IDs, provenance, hashes, and candidate order; passing it does not prove scientific independence.

## 9. Limitations

- 295 distinct formulas are not automatically 295 independent source families or a representative sample of every equation in each domain.
- Calibration guarantees apply only to the declared population and sampling design.
- Applying calibration to Core-15 requires an exchangeability/representativeness assumption; it is not a theorem.
- Per-domain guarantees are not automatically a simultaneous five-domain guarantee.
- Preserve known Core-15 implementation/manuscript discrepancies and disclose them.
- As of this record, no Core-295 catalogue or experiment code exists, and no Core-295 scientific run or Actions dispatch has occurred.

## 10. Implementation gates

### A. Freeze catalogue
- [ ] Declare source universe, inclusion/exclusion, source-family and independence rules.
- [ ] Approve structural-equivalence checks and scientific-review policy.
- [ ] Populate and review 59 valid equations per domain with provenance.
- [ ] Freeze/hash the 295-entry catalogue.

### B. Offline generator and tests
- [ ] Deterministic generation with stable IDs and complete provenance.
- [ ] Separate train/test/extrapolation data and hashes.
- [ ] Duplicate/equivalence, source-family, valid-range, and reproducibility tests.
- [ ] No Core-15 ID collision or calibration leakage.

### C. CI and pipeline
- [ ] Verify exact Core-15 counterparts for all three stages and preserve order.
- [ ] Add the three stage IDs to `run_all.sh` and workflow dispatch/registry.
- [ ] Implement and test deterministic domain-balanced sharding (100 provisional).
- [ ] Keep architecture and per-equation runtime settings unchanged.
- [ ] Add isolated checkpoints/artifacts, exact aggregation, and 295/295 completeness checks.
- [ ] Validate only in dry-run/offline mode before user-authorized dispatch.

### D. Calibration readiness
- [ ] Freeze population, categories, independent unit, and bad-route definition.
- [ ] Predeclare candidate-(\tau) grid and evaluator reference.
- [ ] Freeze/hash training-only calibration records, disjoint from Core-15 evaluation.
- [ ] Pass manifest readiness checks; do not select (\tau) before the user runs calibration and reviews results.

### E. User-run and analysis
- [ ] User explicitly starts the scientific workflow.
- [ ] Review logs, artifacts, checkpoints, coverage, and failures.
- [ ] Analyze outputs only after the user supplies/authorizes them.
- [ ] Report missingness, deviations, and uncertainty; never imply experiments ran without evidence.

## 11. Change control

This record does not authorize merges, branch deletion, history rewriting, workflow dispatch, paid/live API calls, or scientific experiments. Preserve the promotion branch and existing data. Changes to the 295 target, architecture, method settings, sampling design, calibration risk target, or calibration procedure require an explicit recorded decision.


## Structural fingerprinting and equivalence limits

The draft manifest records a deterministic SHA-256 fingerprint generated by parsing the allow-listed canonical expression, declaring variables as real SymPy symbols, applying `sympy.simplify`, serializing with `sympy.srepr`, and hashing the UTF-8 serialization. The manifest records this procedure as `sympy-srepr-simplify-real-symbols-v1`.

This fingerprint is only a reproducible expression-normal-form identifier. It retains symbol names and does not normalize units or dimensions; therefore it is not invariant to variable renaming and is not proof that two equations are structurally distinct. Every candidate still requires explicit equivalence review for symbol/parameter renaming, dimensional conversion, special cases, algebraic rearrangements, limits, derivatives, integrals, solution families and cross-domain analogues. In particular, the proposed Fick flux form must be compared against Fourier and Ohm transport laws before any accepted-equation count.


## Structural-equivalence policy decision pending

The detailed alternatives and audit evidence are consolidated in [CORE295_STRUCTURAL_EQUIVALENCE_POLICY_OPTIONS.md](CORE295_STRUCTURAL_EQUIVALENCE_POLICY_OPTIONS.md). Option C (strict scalar-form equivalence plus complete-system units) is recommended for consideration, but no option has been selected. Until an explicit decision is made, unresolved cross-domain and system-family candidates remain held and the sampling frame remains unfrozen.
