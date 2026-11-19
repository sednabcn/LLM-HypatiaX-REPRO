# HybridSystem V60 migration boundary

## Status

V60 remains opt-in. With v60_activate_native_model=true and a required typed
problem contract, it runs the complete native training-only orchestration:
contract preflight, bounded deterministic template generation, proposal
normalization, scientific gates, single- and multi-basis fold validation,
independent multi-basis evidence verification, objective selection, residual
diagnostics, cross-family finalization, and verified production handoff.
Without explicit activation, V50.2 remains the compatibility path. Normalization creates stable semantic candidate
IDs, deduplicates equivalent expressions, and preserves every contributing
producer record as lineage. The input-proposal processing ceiling is bounded
by the problem's `max_candidates` budget.

V60 now performs a bounded native affine calibration of each normalized
template against the supplied training observations. For each expression it
fits `y ~= scale * expression(X) + offset` by deterministic least squares and
records training RMSE/R², coefficients, fitted expression, status, and failure
reason. Every accepted fit uses every supplied training row; non-finite or
complex predictions are rejected rather than scored on a filtered subset.

This is training-set resubstitution evidence, not cross-validation and not a
selection score. The records are not handed to V50.2 or used to choose a winner.
External LLM/PySR production, scientific gates, fold validation, Pareto
selection, and final evaluation remain on the V50.2 compatibility baseline.
This is a staged migration, not a completed native V60 pipeline or a claim of
improved scientific performance.

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

The native fitting stage:
- Processes at most `min(max_candidates, max_search_attempts)` normalized
  candidates and checks the optional per-discovery wall-time deadline between candidates.
- Uses the restricted expression parser and NumPy evaluation over the complete
  supplied training matrix.
- Fits only a scale and offset by least squares; it does not introduce an
  external symbolic producer or silently drop invalid rows.
- Records training-only resubstitution RMSE/R², coefficients, fitted expression,
  candidate identity, row count, rejection reason, and budget accounting.
- Explicitly records `selection_performed: false`; these metrics are not used
  for retries, ranking, Pareto selection, or far-set evaluation.

Result `implementation_provenance` records:
- `engine_version: 6.0.0`
- `implementation_mode: native_contract_generation_normalization_fitting_v50_2_discovery`
- `native_v60_pipeline: false`
- `native_v60_stages`: contract/run context, bounded template generation,
  expression normalization, semantic identity, deduplication, lineage, and
  bounded training-only affine fitting
- `native_v60_candidate_proposals`: normalized proposals with stable IDs and
  complete producer lineage
- `native_v60_normalization_audit`: rejection and budget accounting
- `native_v60_fitting_audit`: per-candidate training-only fit evidence and
  candidate/time-budget accounting; explicitly not used for selection
- Candidate count and IDs in implementation provenance
- `native_v60_gate_audit`: per-candidate declared scientific gate outcomes,
  including hard/soft severity, unknown-hard counts, and producer lineage;
  no training or far data is consumed and `selection_performed` is false
- `native_v60_training_fit_audit`: bounded training-only affine-fit evidence,
  including coefficients, train metrics, rejection reasons, and budget status;
  `selection_performed` is always false
- `native_v60_multi_basis_fit_audit`: bounded joint fits over small groups of
  normalized basis candidates, with group IDs, term-level coefficients,
  lineage, training metrics, design diagnostics, and budget/rejection audit;
  audit-only, with `selection_performed` false and no far/evaluation data
- `native_v60_multi_basis_evidence_audit`: independently recomputed fold
  coefficients, metrics, rank/condition diagnostics, verified row indices,
  producer lineage, and canonical evidence fingerprints; rejected/tampered
  groups fail closed; audit-only and far-data-free
- `native_v60_multi_basis_validation_audit`: per-group fold metrics,
  independent fold-local joint coefficients, row-index evidence, lineage
  checks, and budget/rejection accounting; audit-only, with
  `selection_performed` false and no far/evaluation data
- `native_v60_training_validation_audit`: per-candidate fold metrics and
  fold-local coefficients, with candidate eligibility inherited from the
  native hard-gate audit; no far/evaluation data is accepted or consumed and
  `selection_performed` is always false
- `native_v60_residual_stability_audit`: per-fold held-out training residual
  summaries and fold-local coefficient stability; diagnostic only, with no
  ranking/selection and no far/evaluation data
- `native_v60_objective_selection_audit`: recomputed fold objectives,
  symbolic complexity, Pareto candidate IDs, selected candidate ID, and
  SHA-256 evidence fingerprints; selection cannot receive far/evaluation data
- `native_v60_contract_preflight` and the data-free `v60_run_context`
- `compatibility_baseline: hybrid_system_v50_2`

## Selection

The reproducibility configuration keeps V50.2 as the default. Callers may
select V60 explicitly with `engine.implementation: "v60"` through the factory
or the Exp2 benchmark runner selector. Unknown selectors fail closed.

## Frozen far-set evaluation boundary

1. Bounded LLM/PySR producer adapters, subject to explicit authorization and
   configured call/token budgets.
2. Hard scientific gates and separately recorded soft diagnostics.
3. Training-only fold evidence, residual diagnostics, and structure stability.
4. Pareto selection with independently verifiable objective evidence.
5. Frozen far-set evaluation after selection.
6. Versioned discovery report and worker-side integrity verification.

Each stage must retain candidate IDs, source provenance, rejection reasons,
budget accounting, and deterministic failure states. The far set must remain
inaccessible to selection and retry logic. Existing worker report contracts
and the Exp2 normalized extrapolation score remain compatibility requirements.

## Migration rules and limitations

- V50.2 remains the default and is not modified by this stage.
- V60 is opt-in; no silent selector fallback is permitted.
- V60 owns contract preflight, bounded template generation, proposal
  normalization/lineage, and bounded training-only affine fitting evidence.
  Scientific gates, fold validation, selection, and discovery output behavior
  remain V50.2.
- Candidate IDs identify canonical symbolic expressions; producer lineage is
  stored separately so deduplication never erases source attribution.
- No benchmark or scientific improvement claim is valid until explicitly
  authorized evaluation provides evidence.
- Do not launch experiments, workers, benchmarks, smoke workflows, or live
  LLM calls as part of architecture implementation.


## Stage 30 — strict candidate-fitting input and deadline validation

The bounded affine-fitting stage now rejects malformed candidate identities
instead of coercing arbitrary values to strings. Candidate IDs and expressions
must be non-empty strings; malformed candidate entries are recorded as
rejected without aborting later candidates. Optional wall-time budgets must
be real, finite, positive numbers, preventing NaN, infinity, booleans, and
string values from bypassing the configured deadline contract.

Regression-test source covers malformed IDs, non-mapping candidate entries,
and invalid deadline values. No tests, CI, experiments, workers, benchmarks,
smoke workflows, or provider calls are run as part of this change.


## Stage 31 — per-call V60 audit state isolation

Every V60 discovery entry point now resets the complete set of native audit,
selection, final-model, far-evaluation, and activation fields before processing
a call. This prevents a later typed or compatibility call from inheriting a
previous call's selected model, production-handoff status, or audit payload.
The reset is centralized and idempotent. Regression-test source covers stale
state clearing and repeated resets. No tests, CI, experiments, workers,
benchmarks, smoke workflows, or provider calls are run as part of this change.


## Stage 32 — native production-result binding

The V60 result annotator's selected-native-model branch now imports the
canonical result builder from the production-handoff module. This makes the
existing handoff code path resolve its result-builder dependency rather than
raising a runtime NameError when native handoff is activated. Regression-test
source verifies the binding is exposed by the V60 integration module. This
does not activate native production handoff or claim that the remaining
selection and evaluation stages are wired into `discover()`.


## Stage 33 — fail closed on unsupported native activation

The v60_activate_native_model metadata flag is now validated as a strict
boolean. Until the complete native gates, fold evidence, selection,
finalization, and frozen evaluation sequence is connected to discover(), an
explicit true request raises NotImplementedError instead of silently
running the V50.2 compatibility discovery path. The default and explicit
false behavior remain on the existing compatibility path. Regression-test
source covers both rejection and flag typing. No tests, CI, experiments,
workers, benchmarks, smoke workflows, or provider calls are run as part of
this change.

## Stage 34 — native V60 training orchestration and separate far evaluation

Explicit metadata[v60_activate_native_model] = true now requires a valid
DiscoveryProblem (or strict discovery_problem_spec) and executes the native
training pipeline instead of delegating to V50.2. The pipeline is connected in
this order:

1. Generate bounded deterministic templates and ingest only caller-supplied
   proposal records; no live LLM or PySR producer is invoked.
2. Normalize proposals, preserve lineage, and run data-independent scientific
   gates. Only candidates with completed eligible hard-gate evidence proceed.
3. Produce single-basis training-fold validation evidence and independently
   verified single-basis objective selection.
4. Fit eligible additive multi-basis groups, validate them within training
   folds, independently recompute their fold evidence, and select only from
   verified evidence.
5. Compute training-fold residual/stability diagnostics without using them as
   a ranking input.
6. Compare the single- and multi-basis winners, refit the selected basis on all
   training rows, and verify the final-model audit before building the outward
   native result.

Native activation fails closed when the typed contract is absent or invalid.
No successful native handoff is reported unless finalization produces a
selected, verified model. The default and explicit-false paths retain the
existing V50.2 compatibility discovery behavior, including the earlier
contract/generation/normalization/fitting audit stages when a typed contract
is supplied.

Far/evaluation arrays are deliberately excluded from discover() and from
DiscoveryProblem. After a successful native finalization, callers may invoke
engine.evaluate_native_far_set(X_far, y_far). This separate method delegates
to the frozen-model evaluator, verifies the final-model audit, evaluates only
the already-selected model, and records selection_changed=false,
selection_performed=false, and explicit no-selection/no-retry far-data flags.
It does not invoke a selector or modify the final-model audit. Far arrays
supplied in native discovery metadata or as discover() keyword arguments are
rejected.

Regression-test source covers typed-contract enforcement, native handoff
without V50.2 fallback, audit-level training/far separation, separate frozen
far evaluation, and rejection before finalization. No tests or CI were run;
no experiments, workers, benchmarks, smoke workflows, or provider calls were
launched as part of this change.
