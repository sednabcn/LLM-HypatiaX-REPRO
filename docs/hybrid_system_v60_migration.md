# HybridSystem V60 migration boundary

## Status

V60 remains opt-in. It now performs typed problem-contract preflight,
captures an immutable data-free run context, generates a bounded deterministic
pool of algebraic templates, and normalizes that pool using the restricted
symbolic-expression parser. Normalization creates stable semantic candidate
IDs, deduplicates equivalent expressions, and preserves every contributing
producer record as lineage. The input-proposal processing ceiling is bounded
by the problem's `max_candidates` budget.

The normalized native pool now also receives a bounded, deterministic affine
least-squares fit against the supplied training arrays. Each candidate is
fitted as scale times its symbolic basis plus an intercept; the stage records
training RMSE/NRMSE/R², coefficients, fit status, and producer lineage. It
rejects candidates that cannot produce finite predictions over every training
row. This fit evidence is audit-only: V50.2 still owns production candidate fitting,
external LLM/PySR production, scientific gates, validation, Pareto selection,
and final evaluation. Native fit metrics do not rank candidates or influence
V50.2 selection. The native V60 gate audit uses only declared constraints and
candidate expressions; unknown hard constraints block eligibility, while soft
failures remain visible without blocking. Candidates that pass hard gates now
receive bounded training-only refit cross-validation: affine coefficients are
re-estimated inside each fold, and held-in fold rows are used only for that
fold's validation metrics. The split strategy can be `kfold` (seeded),
`blocked_kfold`, or expanding-window `time_series`, configured through the
problem's `split_protocol`. This evidence is passed to a separate selector that accepts only normalized
proposals, completed gate outcomes, and fold evidence. The selector verifies
candidate/expression identity, fold completeness, disjoint train/validation row
indices, finite metrics and coefficients, and recomputes aggregate objectives
and symbolic complexity. It forms a three-objective Pareto set (cross-validated
error, fold variability, and symbolic complexity), then applies a deterministic
tie-break within that set. Objective evidence is SHA-256 fingerprinted. The
selector has no training-array or far/evaluation-data parameter; it records
`far_or_evaluation_data_used: false`. This is a staged migration, not a
completed native V60 pipeline or a claim of improved scientific performance.

For calls carrying a typed contract, V60 accepts either:
- `metadata["discovery_problem"]`: an existing `DiscoveryProblem`; or
- `metadata["discovery_problem_spec"]`: a strict JSON-safe mapping parsed by
  `discovery_problem_from_dict()`.

The preflight checks exact variable-name/order alignment, two-dimensional
feature shape, feature width, and one target per feature row. It records a
canonical SHA-256 contract digest plus target/variable identity and input
shapes. It does not retain training values or accept far/evaluation data.
Malformed or misaligned explicit contracts fail closed. Calls without a typed
contract retain the compatibility path.

The normalization stage:
- Parses expressions with the repository's restricted AST-to-SymPy parser and
  rejects undeclared variables or unsupported syntax.
- Uses a simplified symbolic representation for semantic identity, so
  commutative equivalents such as `x + y` and `y + x` share one candidate ID.
- Computes candidate IDs from canonical symbolic identity, independent of
  producer, strategy, or seed.
- Retains original expression, producer-supplied ID, source, strategy, and seed
  for every proposal merged into a deduplicated candidate.
- Records rejected proposal reasons and input-budget truncation counts.
- The normalization operation itself does not inspect targets, training residuals,
  validation folds, or far data.

Result `implementation_provenance` records:
- `engine_version: 6.0.0`
- `implementation_mode: native_contract_generation_normalization_fit_gates_training_validation_objective_selection_v50_2_final_evaluation`
- `native_v60_pipeline: false`
- `native_v60_stages`: contract/run context, bounded template generation,
  expression normalization, semantic identity, deduplication, lineage,
  declared scientific gates, bounded training-only affine fitting,
  bounded training-only refit cross-validation, and verified training-evidence
  objective/Pareto selection
- `native_v60_candidate_proposals`: normalized proposals with stable IDs and
  complete producer lineage
- `native_v60_normalization_audit`: rejection and budget accounting
- Candidate count and IDs in implementation provenance
- `native_v60_gate_audit`: per-candidate declared scientific gate outcomes,
  including hard/soft severity, unknown-hard counts, and producer lineage;
  no training or far data is consumed and `selection_performed` is false
- `native_v60_training_fit_audit`: bounded training-only affine-fit evidence,
  including coefficients, train metrics, rejection reasons, and budget status;
  `selection_performed` is always false
- `native_v60_training_validation_audit`: per-candidate fold metrics and
  fold-local coefficients, with candidate eligibility inherited from the
  native hard-gate audit; no far/evaluation data is accepted or consumed and
  `selection_performed` is always false
- `native_v60_objective_selection_audit`: recomputed fold objectives,
  symbolic complexity, Pareto candidate IDs, selected candidate ID, and
  SHA-256 evidence fingerprints; selection cannot receive far/evaluation data
- `native_v60_contract_preflight` and the data-free `v60_run_context`
- `compatibility_baseline: hybrid_system_v50_2`

## Selection

The reproducibility configuration keeps V50.2 as the default. Callers may
select V60 explicitly with `engine.implementation: "v60"` through the factory
or the Exp2 benchmark runner selector. Unknown selectors fail closed.

## Remaining native V60 stages

1. Bounded LLM/PySR producer adapters and native candidate fitting beyond the
   current single-basis affine least-squares stage.
1. Bounded LLM/PySR producer adapters and richer native candidate fitting
   beyond the current single-basis affine least-squares stage.
2. Training-only residual diagnostics and structure stability.
3. Frozen far-set evaluation after selection, through a separate evaluator.
4. Versioned discovery report and worker-side integrity verification.

Each stage must retain candidate IDs, source provenance, rejection reasons,
budget accounting, and deterministic failure states. The far set must remain
inaccessible to selection and retry logic. Existing worker report contracts
and the Exp2 normalized extrapolation score remain compatibility requirements.

## Migration rules and limitations

- V50.2 remains the default and is not modified by this stage.
- V60 is opt-in; no silent selector fallback is permitted.
- V60 currently owns contract preflight, bounded template generation,
  normalization/lineage, declared scientific gates, training-only affine fitting
  and refit cross-validation, and independently recomputed training-evidence
  Pareto selection. V50.2 still performs production discovery and final
  evaluation; V60 selection is opt-in and remains isolated from far data.
- Candidate IDs identify canonical symbolic expressions; producer lineage is
  stored separately so deduplication never erases source attribution.
- No benchmark or scientific improvement claim is valid until explicitly
  authorized evaluation provides evidence.
- Do not launch experiments, workers, benchmarks, smoke workflows, or live
  LLM calls as part of architecture implementation.
