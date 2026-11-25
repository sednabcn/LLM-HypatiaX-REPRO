# EXP1 — Scientific Value and Redesign

**A consolidated experimental programme for stronger evidence, reproducibility, and lower computational cost**  
**Repository review date:** 25 November 2026

## Executive summary

Exp1 has several scientifically useful but distinct strands: the broad DeFi benchmark, the LLM-sensitive comparison, the Core-15 ablation, fallback-model evaluation, and the PCA-based protocols. The main opportunity is to consolidate their execution infrastructure, provenance, reporting, and shared data preparation without pooling scientifically different cohorts or changing their estimands.

The broad DeFi benchmark is useful for breadth and operational coverage, but its task count must not be presented as the number of independent equation families. Closely related equations, variants, and repeated seeds do not create independent scientific units. A dedicated 30-equation DeFi sensitivity cohort is therefore a meaningful proposed extension if a repository audit confirms it is not already implemented under another name.

The recommended target is one coordinated Exp1 framework with separately declared cohorts, common execution and artifact contracts, and cohort-specific analyses. No benchmark was run as part of this review, and no provider calls or new experimental results are claimed here.

## 1. Design principles

1. **Separate breadth from independent-family evidence.** Report task-level coverage and family-level coverage separately.
2. **Keep scientific cohorts distinct.** Shared tooling is desirable; pooling incompatible populations, splits, arms, or outcomes is not.
3. **Treat seeds as repeated measurements.** Seeds quantify variability; they are not independent equation families.
4. **Make selection leakage-resistant.** Fit preprocessing and select fallback models using training/validation data only. Keep test labels for final evaluation.
5. **Preserve route provenance.** Record the formula, NN, fallback, and selected-predictor metrics separately, along with the actual prediction source.
6. **Keep protocol identity explicit.** Random 80/20 and PCA 40/60 protocols must remain separately labelled and analysed.
7. **Do not optimize the reported score by changing routing policy after seeing test results.**
8. **Minimize cost through orchestration and reuse, not by removing scientifically necessary comparisons.**

## 2. Current Exp1 landscape

### 2.1 Broad DeFi benchmark

The standard DeFi benchmark is a broad task-level evaluation and uses a seeded random 80/20 split. Its PCA counterpart uses a separate 40/60 protocol. These must not be conflated. The broad benchmark is valuable for coverage, debugging, and estimating performance across the registered task catalogue, but its nominal equation count is not evidence of the same number of independent equation families.

The canonical five-seed design discussed in the repository uses seeds **42, 99, 123, 777, and 2024**. The intended provenance workflow validates worker identity, task coverage, hashes, and runtime/configuration consistency. Its aggregate manifest is a provenance/completeness artifact; it should not be described as a scientific aggregate until equation records are joined and cross-seed statistics are calculated.

### 2.2 Existing LLM-sensitive protocol

The existing `experiment_protocol_defi_llm_sensitive.py` defines 21 LLM-sensitive DeFi cases and 6 synthetic controls (27 cases total). It is a useful existing study, but it is not the proposed independent 30-equation DeFi sensitivity cohort. Preserve its original cohort definition and results; do not silently relabel or pad it to 30.

Its preregistered unit of analysis is the equation, with seed-averaged scores per arm. Seeds reduce variance but are not independent units. The primary comparison is the full Hypatia condition against the no-LLM condition in the LLM-sensitive stratum, with paired inference and multiplicity handling as specified by that protocol.

### 2.3 Core-15 ablation

The Core-15 ablation compares `pysr_only`, `hypatia`, and `hypatia_nollm`. It addresses attribution—particularly the contribution of the LLM component—and should remain a distinct cohort and estimand.

The existing analysis uses far-extrapolation outcomes, paired comparisons, and Holm adjustment. Prior aggregate logs indicate incomplete finite far-extrapolation coverage for some equations/arms. Reports should show the complete-case denominator and failures per arm, not only the resulting p-values. Five execution shards are domain partitions, not five independent seeds.

### 2.4 Hybrid fallback candidates

The signed-feature Ridge candidate is now part of the fallback comparison. It is important because DeFi features and targets can be signed, making log-transformed Ridge inapplicable in some cases. Candidate preprocessing and fitting must remain training-only; validation data may select a candidate, while the test set is used once for final evaluation.

Lasso and Elastic Net are natural additional challengers. They should be evaluated under exactly the same seeds, partitions, eligibility rules, and validation procedure as Ridge. Their hyperparameters must not be selected using test performance.

### 2.5 PCA protocols

PCA 40/60 runs are a separate evaluation protocol, not another seed of the standard random 80/20 benchmark. Keep their identifiers, artifacts, and summaries separate. Do not combine their R² values with random-holdout results in a single pooled estimate.

## 3. Scientific value and limitations

### Strengths

- A broad DeFi task catalogue tests practical coverage across multiple financial quantities.
- Multiple seeds expose instability that a single split would conceal.
- The LLM-sensitive protocol isolates sensitivity to naming/description and the LLM contribution.
- Core-15 ablation supports component attribution.
- Hybrid metric provenance and trust-gate diagnostics make it possible to distinguish formula quality from the predictor actually selected.
- Regularized regression candidates provide a transparent, comparatively inexpensive fallback family.

### Limitations to address

- Task counts can overstate independent evidence when several tasks are variants of the same underlying equation family.
- A successful worker run is not equivalent to a completed aggregate analysis.
- A provenance manifest is not a scientific cross-seed aggregation.
- Incomplete or heterogeneous artifact schemas make comparisons difficult unless normalized.
- A single test score is insufficient to explain routing decisions; train/validation/test metrics and route reasons must be retained.
- The existing 27-case LLM-sensitive cohort does not satisfy the separate 30-equation DeFi-family objective.
- PCA and random-holdout results answer different questions and cannot be pooled.

## 4. Proposed 30-equation DeFi sensitivity cohort

Create a **separate, explicitly versioned 30-equation DeFi sensitivity protocol** if the repository audit confirms no equivalent protocol exists. It must not be created by simply renaming the existing 21+6 protocol or by importing the unrelated generic Protocol-30 catalogue.

### Inclusion and independence rules

- Define the target as 30 DeFi equation families, not merely 30 task rows.
- Assign each candidate equation a stable family identifier and a short mathematical definition.
- Record source/reference, domain, input variables, target, units, assumptions, and evaluator implementation.
- Audit algebraic and semantic overlap against the broad DeFi benchmark, the existing 27-case LLM-sensitive protocol, Core-15, and all other registered equation catalogues.
- Treat algebraic rearrangements, parameter variants, and multiple names for the same relationship as one family unless a defensible scientific distinction is documented.
- Keep synthetic controls outside the 30-family primary cohort. If retained, report them as a separate control stratum.
- Publish an inclusion/exclusion ledger before running the study.

### Experimental design

- Preserve the intended LLM-sensitive conditions and define the primary contrast before execution.
- Use the same data-generation and noise rules across arms within each equation.
- Keep evaluator-side ground truth separate from prompts and model outputs.
- Use a fixed, predeclared seed set. Average or otherwise model seed repetitions within equation; do not count seeds as independent units.
- Use paired equation-level comparisons for the primary analysis.
- Predeclare missingness/failure handling, effect sizes, confidence intervals, multiplicity correction, and sensitivity analyses.
- Report both survivor-only and conservative failure-aware results where appropriate.
- Do not tune routing thresholds or degradation parameters against the held-out test outcomes.

The 30-family protocol should be preregistered and independently reviewed before any expensive run. The exact 30 equations must be selected through the family-overlap audit, not guessed from the current task registry.

## 5. Consolidated target architecture

Use one experiment framework with explicit cohort manifests:

| Cohort | Scientific question | Keep separate because |
|---|---|---|
| Broad DeFi benchmark | How well does the system cover the registered DeFi task catalogue? | Task breadth is not independent-family sensitivity evidence |
| DeFi sensitivity-30 | Does the LLM-related intervention improve performance across independent DeFi equation families? | New family-level cohort and preregistered estimand |
| Existing LLM-sensitive-27 | What happens across the existing 21 sensitive cases and 6 controls? | Existing protocol definition and historical comparability |
| Core-15 ablation | What is the contribution of the LLM component and other system components? | Different cohort and attribution question |
| Fallback comparison | Which transparent fallback candidate is robust when NN prediction is unsuitable? | Model-selection question nested within benchmark cases |
| PCA 40/60 | How does the system behave under the PCA partition protocol? | Different split and estimand |

Consolidate the machinery around these cohorts:

- One versioned experiment registry and common equation/family identifiers.
- One runner interface with cohort-specific configuration.
- Shared data generation only where the underlying data protocol is genuinely identical.
- A common artifact schema for run ID, commit/config hashes, cohort, equation ID, family ID, seed, split protocol, arm, metrics, selected predictor, route reason, and failure state.
- One provenance/completeness gate for worker manifests and hashes.
- Separate cohort-specific aggregation and statistical-analysis modules.
- A common report generator that produces separate tables/figures for each cohort and a clearly labelled cross-cohort overview.

This consolidates implementation and operations without pretending the cohorts are one statistical sample.

## 6. Five-seed aggregation

The canonical seed set is **42, 99, 123, 777, 2024**. For every cohort that uses this design:

1. Validate one complete manifest per seed and expected equation/task coverage.
2. Validate stable equation IDs, family IDs, cohort identity, split protocol, commit/config hashes, and artifact hashes.
3. Retain every per-seed record as an immutable input.
4. Join records by cohort, equation ID, arm, and seed.
5. Calculate per-equation across-seed summaries first.
6. Calculate cohort-level summaries over independent equation families, not over raw seed rows.
7. Report the number of equations/families, seeds, successful runs, failures, and exclusions at every stage.
8. Preserve a machine-readable aggregation manifest and a human-readable report.

A five-worker workflow can complete successfully while the scientific aggregation remains unfinished. The pipeline must expose these as separate statuses: execution complete, provenance complete, aggregation complete, and statistical analysis complete.

## 7. Fallback-model comparison

Compare at least:

- Existing log-Ridge where its domain assumptions hold.
- Signed-feature Ridge.
- Lasso.
- Elastic Net.
- Existing NN candidate and existing fallback behavior as controls.

Use identical train/validation/test partitions and seed assignments. Fit scalers on training data only. Select candidate and hyperparameters using validation data only. Refit the selected candidate on the full training partition and evaluate once on the untouched test partition.

Record eligibility, validation score, selected candidate, hyperparameters, fit failures, train/test predictions, and the final prediction source. Do not compare only the best test score across candidates. Report selection frequency and performance distributions across equations and seeds.

## 8. Cost-reduction strategy

Reduce cost without weakening the evidence:

- Generate and validate deterministic datasets once per equation/seed/split when arms can legitimately share them.
- Reuse cached non-LLM computations across description-only conditions where cache keys prove the computation is identical.
- Run cheap schema, evaluator, and synthetic-control checks before expensive provider or symbolic-regression jobs.
- Use staged execution: smoke test, small pilot, full cohort.
- Allocate expensive runs only to preregistered arms and seeds.
- Avoid rerunning the broad benchmark merely to obtain a sensitivity result that belongs to the dedicated 30-family cohort.
- Keep one canonical five-seed orchestration path per cohort; retire duplicate entry points only after equivalence and artifact lineage are demonstrated.
- Store immutable per-seed outputs so aggregation/reporting changes do not require rerunning model calls.
- Publish runtime, token/provider usage, and compute cost per cohort and per equation family.

Cost savings must not come from dropping independent families, reducing the seed set after seeing results, pooling incompatible splits, or weakening failure accounting.

## 9. Implementation roadmap

### Phase 1 — Repository and lineage audit

- Inventory every Exp1 runner, protocol, workflow, registry, result directory, and aggregate.
- Map each experiment name to its actual script, cohort, arms, split, seeds, and outputs.
- Build an equation-family overlap matrix across all catalogues.
- Trace historical artifacts to exact workflow run, commit, config, and code hashes.
- Measure actual compute/provider cost and identify duplicated work.

**Exit criterion:** an evidence-backed map of what exists, what is scientifically distinct, what is duplicated, and what is missing.

### Phase 2 — Protocol specification

- Select and document 30 independent DeFi equation families.
- Freeze the sensitivity-30 estimand, arms, data protocol, seed set, exclusions, failure handling, and statistical plan.
- Decide explicitly how the existing 27-case study relates to the new cohort; preserve it unchanged for historical comparison.
- Review the specification before implementation.

**Exit criterion:** versioned protocol and inclusion/exclusion ledger approved before expensive execution.

### Phase 3 — Shared infrastructure

- Standardize configuration and artifact schemas.
- Separate worker completion from provenance, aggregation, and analysis statuses.
- Implement deterministic aggregation keyed by cohort/equation/family/arm/seed.
- Add integrity and regression tests for route provenance and leakage prevention.

**Exit criterion:** reproducible end-to-end dry run using fixtures, without provider calls.

### Phase 4 — Controlled execution

- Run a small pilot to verify data, evaluator, and artifact contracts.
- Execute the preregistered cohort/arms/seeds only after explicit run authorization.
- Record cost and failure data.
- Do not change protocol or routing based on interim test outcomes.

**Exit criterion:** all required outputs and provenance gates complete.

### Phase 5 — Analysis and publication

- Generate cohort-specific summaries and uncertainty estimates.
- Report independent-family denominators and all exclusions.
- Compare fallback candidates under the locked validation protocol.
- Produce a consolidated report with separate scientific conclusions for each cohort.

**Exit criterion:** analysis is reproducible from committed artifacts and scripts.

## 10. Risks and safeguards

| Risk | Safeguard |
|---|---|
| Inflated sample size from related equations | Family IDs and overlap audit; family-level inference |
| Seeds treated as independent units | Aggregate within equation before cohort-level inference |
| Mixing random and PCA splits | Immutable split-protocol labels and separate reports |
| Incomplete shards hidden by old artifacts | Strict run-scoped artifact aggregation |
| Test leakage in fallback selection | Validation-only selection and untouched test evaluation |
| LLM contribution overstated | Preserve named/neutral and no-LLM controls with preregistered contrasts |
| Cost reduction weakens science | Optimize orchestration/reuse, not cohorts or failure criteria |
| Historical artifacts differ in schema | Versioned schema and explicit migration/compatibility checks |

## 11. Decisions

1. Keep the broad DeFi benchmark as a breadth/coverage study, but report independent-family counts separately.
2. Keep the existing 21+6 LLM-sensitive protocol unchanged.
3. Create the separate DeFi sensitivity-30 protocol only after a family-overlap audit confirms the 30 independent units.
4. Keep Core-15 ablation as a distinct attribution study.
5. Keep PCA 40/60 results separate from random 80/20 results.
6. Use one canonical five-seed workflow per cohort and implement a real scientific aggregation stage after provenance validation.
7. Evaluate Ridge, Lasso, and Elastic Net under a common leakage-resistant selection protocol.
8. Keep `degradation_tau: null` unchanged unless a separately justified, preregistered calibration study is authorized; tau calibration is not a goal of this redesign.
9. Do not launch expensive runs or provider calls as part of the design/documentation phase.

## Appendix A — Evidence boundaries

This report distinguishes repository facts from recommendations. The repository contains the broad DeFi benchmark, the 21-sensitive-plus-6-control LLM-sensitive protocol, Core-15 ablation machinery, the signed-feature Ridge candidate, and separate PCA protocols. The proposed independent 30-equation DeFi sensitivity cohort, unified cohort orchestration, complete scientific aggregation stage, and Lasso/Elastic Net comparison are recommendations, not claims of completed implementation.

A successful CI check validates the code paths exercised by that check; it does not establish that a full benchmark was rerun, that all cohorts were aggregated, or that scientific performance improved.

## Appendix B — Minimum artifact fields

Each equation/arm/seed record should include:

- `schema_version`, `run_id`, `commit_sha`, `config_hash`, `runtime`
- `cohort_id`, `protocol_version`, `equation_id`, `family_id`, `domain`
- `seed`, `split_protocol`, `train/test` sizes and split/data hashes
- `arm_id`, `model/configuration`, `evaluator_version`
- formula/LLM/NN/fallback metrics, selected-predictor metrics, and prediction-source provenance
- trust-gate diagnostics, candidate eligibility, validation scores, and route reason
- success/failure state, structured failure reason, runtime, token/provider usage, and cost
- artifact hash and aggregation inclusion/exclusion status
