# HybridDiscoverySystem: Physics-Informed Architecture Redesign

**Status:** design proposal; documentation only  
**Related implementation:** [PR #177](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/177)  
**Intended base:** `hybrid/fix-llm-lifecycle-and-candidate-selection` (PR #177 head)  
**Scope:** architecture, scientific requirements, interfaces, validation policy, rollout, and open decisions. This document does not claim that the proposed pipeline is implemented.

![HybridDiscoverySystem architecture](images/hybrid-discovery-physics-informed-architecture.svg)

## 1. Executive summary

The current `HybridDiscoverySystem` is closer to a symbolic-regression retry wrapper than a complete physics-informed equation-discovery system. Its recent lifecycle and complexity-aware selection fixes (PR #177) are useful first steps, but selection still relies mainly on training (R^2) plus a heuristic complexity screen. It does not yet establish generalization through independent training-only validation, enforce a comprehensive scientific problem contract, or systematically compare physical plausibility and stability.

The proposed system is a staged, auditable pipeline:

1. Specify the scientific problem and the assumptions that are actually known.
2. Generate hypotheses using bounded LLM assistance and/or domain templates.
3. Search and fit candidates using symbolic regression.
4. Normalize candidates and apply hard symbolic, dimensional, domain, physical, and numerical gates.
5. Evaluate surviving candidates using repeated, seeded validation splits drawn only from the training region.
6. Select and retain a Pareto set across predictive performance, simplicity, physical consistency, and stability.
7. Evaluate the selected model once on the sealed far-extrapolation region, without feeding that result back into discovery or selection.
8. Return a structured report including alternatives, evidence, uncertainty, limitations, and provenance.

**Core principle:** LLM proposes; symbolic search fits; explicit scientific validators gate; held-out training evidence selects; far data evaluates once.

## 2. Current-state diagnosis

### 2.1 Current behavior

The existing implementation has a retry loop around the symbolic engine. It records candidate expressions and quality checks, selects a candidate primarily using training (R^2), and can fall back to `PhysicsAwareRegressor`. PR #177 improves this by keeping the LLM engine alive across retries, excluding invalid/sentinel results, preferring candidates that pass the current complexity screen, and using simplicity as a tie-break.

### 2.2 Remaining architectural gaps

| Gap | Consequence | Required redesign |
|---|---|---|
| Training fit is the main selection signal | High training fit can reward overfit or unstable equations | Repeated internal validation using training-region data only |
| Complexity is a heuristic warning/gate | A heuristic alone is not a scientific validity test | Explicit complexity objective plus separate scientific gates |
| Physical constraints are not a complete contract | Dimensionally valid expressions can still violate physics | Declare hard constraints, soft diagnostics, and unknown assumptions |
| Retry attempts can be near-duplicates | Compute/API budget is spent without meaningful search diversity | Strategy-aware search portfolio and duplicate detection |
| LLM role and cost are not sufficiently bounded | Retries can imply repeated model calls and opaque provenance | Separate proposal stage, cache/deduplicate, explicit call budget |
| One winner hides trade-offs | A slightly better fit can dominate a simpler, more stable model | Preserve a ranked Pareto set |
| Failure can be conflated with weak success | A poor candidate may appear as a discovered equation | Explicit no-credible-candidate outcome and rejection reasons |
| Far-set handling is easy to misuse | Repeated inspection can leak test information into selection | Sealed final evaluation boundary and provenance assertions |

## 3. Target architecture

See the architecture image above. The conceptual stages are:

### Stage 0 — DiscoveryProblem contract

Represent the scientific task explicitly rather than passing disconnected dictionaries through the pipeline.

Proposed fields:

- Target and independent-variable names, descriptions, and canonical units.
- Training data and immutable split metadata.
- Domain identifier and domain-specific assumptions.
- Variable domains and bounds (positive, non-negative, bounded, probability, etc.).
- Hard physical constraints and soft scientific expectations.
- Known invariants, symmetries, conservation laws, monotonicity, and limiting behavior where justified.
- Allowed symbolic operators and forbidden operations.
- Noise assumptions, tolerances, and measurement precision.
- Reproducibility seed, software/configuration versions, and compute budgets.
- Explicit boundary marking the far-extrapolation data as evaluation-only.

Unknown assumptions must remain unknown. Do not infer positivity, conservation, monotonicity, or a physical law solely from variable names. Every constraint should carry its source, severity, applicability, and evidence.

### Stage 1 — Hypothesis generation

The LLM is a hypothesis generator, not an authority or final selector.

It may produce structured proposals containing:

- Candidate expression or expression template.
- Expected operator families and transformations.
- Physical rationale and assumptions.
- Expected dimensions and limiting behavior.
- Confidence and known caveats.
- A traceable proposal identifier.

Controls:

- Bound the number of calls, tokens, latency, and retries.
- Cache or deduplicate equivalent proposals.
- Record requested/actual model mode, call status, replay status, errors, and sanitized provenance.
- Treat malformed or unsupported proposals as rejected inputs.
- Never allow LLM confidence to override hard validators or measured evidence.
- Provide a deterministic non-LLM route.

A proposal should be converted into a constrained search hint, not accepted as a fitted result. The system should make clear whether a candidate originated from an LLM proposal, a domain template, an unconstrained search, or a hybrid search.

### Stage 2 — Symbolic candidate search

Run a portfolio of meaningfully different search strategies rather than merely repeating the same search with a new seed.

Potential strategies:

- LLM-proposed operator/template seeds.
- Domain-template or invariant-derived seeds.
- Constrained PySR search with explicit grammar.
- Alternative operator subsets or complexity budgets.
- Residual-guided search to model unexplained structure.

Each strategy must have an explicit resource budget and reproducible seed. Search attempts should be deduplicated by normalized symbolic form. Candidate generation must be separated from candidate evaluation and final selection.

### Stage 3 — Candidate normalization and hard validation gates

Normalize expression syntax and variable naming before evaluation. Retain the original expression for audit.

Hard gates should be applied in a traceable order:

1. Parseability and supported symbolic operations.
2. No undefined variables, sentinel expressions, or non-finite constants.
3. Dimensional consistency using canonical units and explicit unit metadata.
4. Domain restrictions, including singularities and invalid input regions.
5. Numerical safety: finite outputs, no unintended overflow/underflow, and controlled behavior near singularities.
6. Explicit physical constraints supplied by the problem contract.

Physical checks may include, where scientifically justified:

- Positivity or non-negativity.
- Conservation/invariant residuals.
- Symmetry or exchange invariance.
- Monotonicity over a declared domain.
- Limiting/asymptotic behavior.
- Boundary conditions.
- Sign and range constraints.
- Known structural identities.

A constraint evaluator must distinguish:
- **pass** — the candidate was checked and passed;
- **fail** — the candidate violated a hard requirement;
- **warning** — a soft expectation is questionable;
- **not_applicable** — the check does not apply;
- **unknown/not_checked** — evidence or metadata was unavailable.

Do not silently convert warnings into passes. Do not penalize a candidate for a physical law that was never declared. A candidate that fails a hard constraint is ineligible for selection, with a machine-readable rejection reason.

The existing `EnsembleValidator`, `DimensionalValidator`, `DomainValidator`, and `SymbolicValidator` should be audited and reused where their semantics are sound. Their aggregate score must not substitute for inspectable per-check results.

### Stage 4 — Training-only evaluation

All model fitting and candidate selection must use data from the training region. Divide that region into reproducible fitting/validation partitions.

Recommended evaluation:

- Repeated seeded holdouts or cross-validation appropriate to sample size.
- Range-aware splits where the scientific question requires testing interpolation near the edge of the observed domain.
- Fit every candidate only on each fold's fitting partition.
- Evaluate on that fold's held-out training-region partition.
- Record mean, median, spread, worst-fold behavior, and valid-fold count.
- Record residual structure, heteroscedasticity indicators, and numerical failures.
- Measure expression stability across folds and seeds, including symbolic equivalence where feasible.

Do not use the far-extrapolation set for early stopping, hyperparameter tuning, operator selection, LLM prompting, candidate filtering, tie-breaking, or retry decisions.

If the available training sample is too small for reliable repeated validation, report that limitation and use a predeclared alternative (for example, leave-one-out where appropriate). Never present an unstable estimate as strong validation evidence.

### Stage 5 — Multi-objective selection

First apply hard eligibility gates. Then compare eligible candidates across distinct objectives:

- Predictive error on internal held-out training data (scale-normalized and with units/scale stated).
- Variability/worst-fold performance.
- Symbolic complexity (node count, operator cost, nesting, and/or description length).
- Physical consistency and soft-constraint diagnostics.
- Stability across splits/seeds and sensitivity to perturbations.
- Numerical robustness over the declared valid input domain.

Use Pareto dominance to preserve meaningful trade-offs rather than hiding all objectives inside one opaque weighted score. If a single recommendation is needed, use a documented, predeclared tie-break policy and retain the full Pareto set.

Do not compare raw errors across differently scaled targets without normalization. Keep metric definitions, units, null semantics, and lower/higher-is-better direction explicit.

### Stage 6 — Sealed far-extrapolation evaluation

The far region is a final evaluation set. It is not part of candidate discovery.

- Freeze the candidate set, selection policy, and selected equation before far evaluation.
- Evaluate the selected candidate and, if useful for reporting, the already-frozen Pareto alternatives.
- Do not use far metrics to revise the selected model or rerun discovery.
- Record far metrics as evaluation outputs only.
- Mark the run as contaminated if far data was used in any selection decision.

For Exp2, preserve the normalized score contract already introduced: `extrapolation_score = RMSE_far / std(y_train)`, with explicit null/status behavior when training target scale is invalid or zero. Keep legacy `error_pct` clearly marked as legacy and never use it for selection.

### Stage 7 — DiscoveryReport

Return a structured report rather than only an expression and training (R^2).

Suggested report fields:

- `status`: `accepted`, `provisional`, or `no_credible_candidate`.
- Selected equation and normalized symbolic representation.
- Ranked/Pareto candidate alternatives.
- Candidate source and search strategy.
- Hard-gate outcomes and rejection reason codes.
- Per-objective metrics, units, folds, spread, and valid sample counts.
- Complexity and stability diagnostics.
- Physical assumptions, checks applied, checks not applicable, and unknowns.
- Residual and numerical diagnostics.
- LLM provenance and call-budget accounting.
- Seeds, config, engine versions, and software provenance.
- Training-only selection evidence.
- Separate final far-evaluation metrics and an explicit flag that they were not used for selection.
- Limitations and confidence statement.

If no candidate passes the hard gates or the predeclared minimum evidence requirements, return `NO_CREDIBLE_CANDIDATE`. A low-quality expression may be retained as a diagnostic artifact, but must not be represented as a successful discovery.

## 4. Suggested component boundaries

These are conceptual responsibilities, not claims that the classes already exist.

| Component | Responsibility |
|---|---|
| `DiscoveryProblem` | Immutable scientific/data contract, units, constraints, budgets, split boundaries |
| `HypothesisGenerator` | Bounded LLM and template-based structured proposals |
| `CandidateSearch` | PySR/search portfolio, seeds, strategy tracking, duplicate detection |
| `CandidateNormalizer` | Canonical parse/representation and expression identity |
| `PhysicsConstraintEvaluator` | Hard constraints and soft scientific diagnostics |
| `CandidateEvaluator` | Training-only folds, predictive/stability/residual metrics |
| `ParetoSelector` | Eligibility, Pareto front, transparent final tie-break |
| `DiscoveryReport` | Full result, alternatives, audit trail, uncertainty, final test metrics |

Suggested candidate record:

```python
{
    "candidate_id": "...",
    "expression": "...",
    "normalized_expression": "...",
    "source": "llm_proposal|domain_template|pysr_search|residual_search",
    "search_strategy": "...",
    "seed": 42,
    "hard_constraints": {
        "dimensional_consistency": {"status": "pass"},
        "domain_validity": {"status": "pass"},
        "physical_invariants": {"status": "unknown"},
        "numerical_safety": {"status": "pass"}
    },
    "training_validation": {
        "metric_name": "...",
        "fold_scores": [],
        "mean": None,
        "spread": None,
        "worst_fold": None
    },
    "complexity": {"node_count": None, "operator_cost": None},
    "stability": {"equivalent_across_folds": None},
    "eligible": False,
    "rejection_reasons": []
}
```

Exact schemas should be settled during implementation and versioned for benchmark compatibility.

## 5. Selection policy and safeguards

Recommended order:

1. Reject malformed, unsupported, non-finite, or sentinel candidates.
2. Reject candidates that violate a declared hard constraint.
3. Require a minimum amount of valid training-only validation evidence.
4. Compute predictive, complexity, physical, and stability objectives independently.
5. Construct the Pareto set.
6. Apply a documented tie-break only if a single default equation is required.
7. Freeze selection before any far-set evaluation.

The current PR #177 policy (prefer candidates that pass the existing complexity screen, then training (R^2), with a simplicity tie-break) remains a transitional improvement, not the target final selection policy.

## 6. Reproducibility, budgets, and provenance

Every run should record:

- Input-data fingerprint or stable dataset identifier (without exposing sensitive data).
- Training/far split definition and split seed.
- DiscoveryProblem version and constraint-source metadata.
- Search engine/version/configuration, operator grammar, and per-strategy seeds.
- LLM provider/model/mode, whether a call was attempted/completed/replayed, proposal IDs, and sanitized error details.
- LLM call/token/latency budget and actual usage where available.
- Candidate counts at each stage and rejection counts by reason.
- Fold definitions, validation metrics, selector version, and tie-break policy.
- Final selected candidate ID and immutable candidate-set fingerprint.
- Far evaluation timestamp/stage and explicit `used_for_selection: false`.

Retries should be budgeted by total search cost, not merely attempt count. A timeout should not automatically trigger another equivalent expensive search. LLM proposals should be cached/deduplicated where safe; the number of LLM calls should be an explicit configuration, not an accidental consequence of retry count.

## 7. Failure states

Use explicit outcomes, for example:

- `INVALID_PROBLEM_SPECIFICATION`
- `NO_CANDIDATES_GENERATED`
- `ALL_CANDIDATES_FAILED_SYMBOLIC_VALIDATION`
- `ALL_CANDIDATES_FAILED_PHYSICAL_GATES`
- `INSUFFICIENT_VALIDATION_EVIDENCE`
- `NO_CREDIBLE_CANDIDATE`
- `SEARCH_BUDGET_EXHAUSTED`
- `LLM_UNAVAILABLE_FALLBACK_USED`
- `ACCEPTED_WITH_WARNINGS`
- `ACCEPTED`

Failure should preserve candidate and diagnostic artifacts where possible, but it must not silently downgrade into a success state.

## 8. Testing strategy (CI only)

Tests should be offline and deterministic. No live LLM calls, worker launches, benchmark runs, or external API calls should be required for ordinary regression coverage.

Recommended test layers:

1. **Unit tests:** expression normalization, candidate identity, constraint result semantics, dimensional checks, Pareto dominance, tie-break determinism, null/invalid metric handling.
2. **Scientific synthetic tests:** known equations with known units, invariants, symmetries, limiting behavior, and deliberately invalid alternatives.
3. **Leakage tests:** prove that far-set values cannot affect candidate ranking, early stopping, prompt content, or selector output.
4. **Validation tests:** repeated splits are deterministic under fixed seeds; fold metrics aggregate correctly; insufficient sample cases are explicit.
5. **LLM contract tests:** mocked proposal responses, unavailable provider, malformed proposal, duplicate proposals, call-budget enforcement, and deterministic non-LLM fallback.
6. **Provenance tests:** every candidate has source/strategy/seed and every rejection has a reason.
7. **Integration tests:** end-to-end synthetic pipeline with mocked search/LLM components and no network or worker execution.
8. **Exp2 compatibility tests:** preserve existing row-level audit artifacts and normalized extrapolation score semantics.

CI must be the execution venue. Do not add experiment or smoke workflow launches as part of this documentation change.

## 9. Migration plan

### Phase A — Contracts and auditability
- Define versioned `DiscoveryProblem`, candidate, constraint-result, and report schemas.
- Preserve the current public `discover()` interface through an adapter.
- Add candidate IDs, source/strategy metadata, and explicit failure statuses.
- Keep PR #177 lifecycle/complexity fixes intact.

### Phase B — Independent training validation
- Implement seeded internal folds and candidate-level validation.
- Add leakage guards that make far data inaccessible to the selector.
- Record predictive spread, worst-fold metrics, and stability.
- Keep current selector behind a versioned compatibility option during migration.

### Phase C — Physics-informed gates
- Compose existing validators through typed per-check outcomes.
- Add domain-specific constraints only when declared in the problem contract.
- Add synthetic tests for dimensional and physical counterexamples.
- Separate hard failures from soft warnings and unknown checks.

### Phase D — Pareto selection and report
- Implement multi-objective Pareto ranking.
- Retain alternatives and transparent tie-break rationale.
- Add `NO_CREDIBLE_CANDIDATE` and structured report output.
- Keep legacy benchmark fields available while adding versioned fields.

### Phase E — Search and LLM orchestration
- Separate proposal generation from search attempts.
- Add bounded/cached LLM proposals and total budget accounting.
- Add strategy-aware search diversity and duplicate detection.
- Make pure symbolic fallback deterministic and auditable.

### Phase F — Scientific evaluation (only when explicitly authorized)
- After implementation and CI review, run approved synthetic/benchmark experiments.
- Compare the redesigned selector against the historical baseline.
- Evaluate interpolation and far extrapolation separately.
- Report per-equation/direction coverage and all failed/invalid cases.
- Do not launch these experiments without explicit authorization.

## 10. Non-goals and scientific caveats

- This architecture does not guarantee discovery of the true governing equation.
- Dimensional consistency is necessary in many physical settings but is not sufficient for physical correctness.
- A candidate can satisfy known constraints and still be wrong outside the observed domain.
- LLM-generated rationales are hypotheses, not evidence.
- Pareto optimality is relative to the objectives and candidate pool; it does not establish truth.
- Extrapolation performance is empirical evidence on the evaluated range, not a proof of behavior at arbitrary distances.
- Domain-specific constraints must be supplied and reviewed by someone with appropriate scientific knowledge.
- The redesign must not optimize repeatedly against the far set.

## 11. Repository integration notes

- PR #177 is the implementation baseline for LLM lifecycle persistence and the interim complexity-aware selector.
- This document is a design specification only; it does not alter the runtime behavior.
- The Exp2 normalized score contract remains: `extrapolation_score = RMSE_far / std(y_train)`, with explicit status/null semantics.
- Keep legacy `error_pct` for compatibility but do not promote it as the primary score.
- Keep REPRO responsible for reproducible experiment sources/workers. Any post-run comparative analysis belongs in DEV.
- No experiments, smoke runs, workers, benchmarks, LLM API calls, or tests are launched by this documentation change.

## 12. Acceptance criteria for the future implementation

The redesign should not be considered complete until:

- [ ] Problem assumptions, units, domains, and constraints are explicit and versioned.
- [ ] Candidate provenance and rejection reasons are complete.
- [ ] Hard physical/dimensional/domain checks are separate from soft diagnostics.
- [ ] Candidate selection uses repeated training-only validation, not training fit alone.
- [ ] The far set is inaccessible to selection and leakage tests prove this.
- [ ] Candidate selection is multi-objective and retains a Pareto set.
- [ ] LLM usage has explicit budgets, deduplication, and a deterministic fallback.
- [ ] No-credible-candidate is a first-class outcome.
- [ ] Offline CI tests cover contracts, scientific constraints, stability, leakage, and provenance.
- [ ] Benchmark outputs preserve the Exp2 normalized score contract.
- [ ] No claim of scientific improvement is made until authorized experiments provide evidence.


---

## 13. Implementation log — candidate validation gates

This section records the implementation sequence and the boundary between completed code and remaining architecture work. It supplements the target design above; it does not claim that the full redesign is complete.

### 13.1 Step 1 — typed problem and candidate contracts

The implementation uses the existing versioned contracts in `hypatiax/tools/symbolic/discovery_contracts.py`:

- `DiscoveryProblem` carries target identity/unit, variable names/units/domains, declared constraints, operator allowlists, split protocol, budget, and metadata.
- `ConstraintSpec` declares a constraint identifier, kind, severity, and parameters.
- `ConstraintOutcome` records pass/fail/warning/not-applicable/unknown/not-checked, severity, reason, and evidence.
- `CandidateRecord` carries normalized expression, source, search strategy, seed, constraint outcomes, rejection reasons, eligibility, and deterministic candidate identity.
- `DiscoveryReport` is the intended structured report envelope, including selected and Pareto candidate identifiers and a segregated far-evaluation field.

The contracts are explicit: no unit, positivity, symmetry, or physical law is inferred from a variable's spelling. Callers must supply the scientific assumptions they want enforced.

### 13.2 Step 2 — standalone candidate validator

Added `hypatiax/tools/symbolic/discovery_validation.py` and exported `CandidateValidator` from the symbolic package.

The validator performs these gates:

1. Restricted mathematical parsing using the repository's safe SymPy parser.
2. Rejection of invalid and non-finite symbolic expressions.
3. Dimensional analysis through the existing `DimensionalValidator` when units are declared, including comparison with the declared target unit.
4. Explicit domain checks for `positive_output`, `nonnegative_output`, and `finite_output`.
5. Explicit even/odd symmetry checks for a named variable, only when the declared sampling interval is symmetric about zero.
6. Auditable per-check outcomes and rejection reasons.

Domain checks use a deterministic Cartesian grid built from declared finite variable bounds, capped by `sample_limit` (default 512). This is a screening test, not a proof over a continuous domain. A hard constraint that cannot be evaluated is `unknown` and blocks eligibility; missing evidence never silently passes a hard gate. Unsupported constraint kinds are also unknown rather than guessed.

When no units or constraints are declared, the corresponding built-in checks are marked `not_applicable`. This preserves a clear distinction between “checked and passed” and “not specified.”

### 13.3 Step 3 — offline regression coverage

Added `tests/test_physics_informed_candidate_validation.py` with cases for:

- A declared nonnegative-output constraint passing and being recorded.
- A strict-positive constraint rejecting a zero boundary.
- An unevaluable hard constraint producing unknown and blocking eligibility.
- An unsafe/untrusted expression being rejected by the restricted parser.

These tests were added to the repository but were not run locally by the implementation agent. No CI run is implied by their presence.

### 13.4 Step 4 — connect gates to live retry selection

The next integration change is in `hypatiax/tools/symbolic/hybrid_system_v50_2.py`.

- The public `discover(..., metadata=...)` adapter accepts an optional typed `metadata["discovery_problem"]` value.
- The value must be a `DiscoveryProblem` instance. A plain dictionary is rejected rather than being guessed/coerced into scientific assumptions.
- The active problem is reset on every public call, preventing a reused engine from accidentally carrying one equation's constraints into the next.
- Each valid PySR retry candidate is passed through `CandidateValidator` before it can enter the clean or complexity-flagged selection pools.
- Failed or unknown hard gates exclude the candidate from selection and are attached to the attempt result as `candidate_validation` and `candidate_validation_status`.
- Early stopping is permitted only for a candidate that passes the declared gates.
- The optional PhysicsAwareRegressor fallback is subjected to the same declared gates before it can replace the symbolic result.
- If every candidate fails a configured hard gate, no rejected candidate is promoted as a valid discovery.

The existing complexity heuristic remains a secondary preference after scientific eligibility. Training R² remains the interim score within the eligible pool. Far/test metrics are not passed to the validator and are not used by this gate or retry selection.

**Compatibility mode:** If `discovery_problem` is omitted, the legacy retry path remains active and candidate validation is marked `not_configured`. This is deliberate during migration: old benchmark callers have not yet been updated to supply complete units/domains/constraints. A run without a problem contract must not be described as having passed physics-informed gates.

### 13.5 Current limitations after this integration

- Candidate validation is opt-in until benchmark and application callers construct and pass a complete `DiscoveryProblem`.
- The validator currently implements only the listed built-in constraint kinds. Conservation laws, invariants, limiting behavior, monotonicity, and more advanced domain predicates require explicit typed extensions and tests.
- Deterministic finite-grid checks can miss violations between sample points and can reject a valid candidate if a sampled point lies on a singularity. Evidence must always state the sampling protocol.
- Dimensional analysis depends on the existing validator's supported unit grammar and inference behavior. An unknown or missing required unit result blocks a declared hard dimensional gate.
- The retry selector still uses the existing training-R²/complexity policy among candidates that pass gates. Repeated held-out training validation, expression stability, and Pareto selection are not implemented by this step.
- The report envelope is not yet the sole public return format; legacy result dictionaries remain for compatibility.
- The far set remains outside this implementation path. A separate evaluation-only adapter is still needed to make the “sealed far set” boundary architectural rather than merely a caller convention.

### 13.6 Next implementation steps

1. Update REPRO benchmark adapters to construct typed `DiscoveryProblem` instances from authoritative equation metadata, units, ranges, and reviewed constraints; do not invent constraints where metadata is absent.
2. Add training-only repeated/blocked holdout evaluation and leakage tests. The selector must receive training folds only; the far set must not be present in its function signature.
3. Record candidate predictions and fold-level evidence, then measure expression stability across seeds/folds.
4. Add additional declared physical predicates (invariants, symmetry groups, limiting cases) with explicit unknown/fail semantics and counterexample tests.
5. Implement multi-objective Pareto ranking over validation error, complexity, physical consistency, and stability, retaining alternatives and rationale.
6. Produce `DiscoveryReport` as the structured result while preserving legacy fields during migration.
7. Add CI-only regression coverage and inspect CI results before any experiment is considered.
8. Only after the implementation and CI review, request explicit authorization before launching any smoke, benchmark, worker, or LLM-backed experiment.

### 13.7 Change provenance

- Candidate validation module and tests were introduced in PR #180, which GitHub reports merged into the #177 implementation branch.
- Retry/fallback integration and this documentation update are being developed as the next stacked implementation change on the #177 branch.
- PR #177 remains the implementation baseline until merged to `master`; PR #178 contains the original architecture specification and remains a separate documentation PR at the time of this update.
- No experiment, smoke workflow, benchmark, worker, local test, CI workflow, or LLM API call was launched for these implementation changes.
