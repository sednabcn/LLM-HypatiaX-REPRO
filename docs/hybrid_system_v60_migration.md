# HybridSystem V60 migration boundary

## Status

V60 remains opt-in. With v60_activate_native_model=true and a required typed
problem contract, it runs the complete native training-only orchestration:
contract preflight, bounded deterministic template generation, proposal
normalization, scientific gates, single- and multi-basis fold validation,
independent multi-basis evidence verification, objective selection, residual
diagnostics, cross-family finalization, and verified production handoff.
Without explicit activation, V50.2 remains the compatibility path.
Normalization creates stable semantic candidate IDs, deduplicates equivalent
expressions, and preserves every contributing producer record as lineage. The
input-proposal processing ceiling is bounded by the problem's `max_candidates`
budget.

V60 now performs a bounded native affine calibration of each normalized
template against the supplied training observations. For each expression it
fits `y ~= scale * expression(X) + offset` by deterministic least squares and
records training RMSE/R², coefficients, fitted expression, status, and failure
reason. Every accepted fit uses every supplied training row; non-finite or
complex predictions are rejected rather than scored on a filtered subset.

This affine-fit audit is training-set resubstitution evidence, not
cross-validation and not a selection score. Native selection uses the
separate training-fold validation and independently checked objective
evidence described in Stage 34. V60 ingests only caller-supplied LLM/PySR
proposal records; it does not invoke live external producers. This integration
does not constitute a scientific performance claim.

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

The training-only native selection and finalization stages are connected in
Stage 34. Far-set evaluation is a separate post-finalization call to
evaluate_native_far_set(X_far, y_far); the far arrays never enter discover(),
the typed problem contract, candidate gates, fold validation, selectors, or
retry logic. Existing worker report contracts and the Exp2 normalized
extrapolation score remain compatibility requirements.

## Migration rules and limitations

- V50.2 remains the default and is not modified by this stage.
- V60 is opt-in; no silent selector fallback is permitted.
- Without explicit v60_activate_native_model=true, V50.2 remains the default
  discovery implementation.
- With explicit activation and a typed DiscoveryProblem, V60 owns the complete
  bounded training-only gate/validation/selection/finalization pipeline.
- Far evaluation is always a separate post-finalization API call.
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

At this stage the v60_activate_native_model metadata flag was validated as a
strict boolean and explicit true was rejected until orchestration existed.
Stage 34 supersedes that guard by connecting the complete training-only
pipeline. The strict boolean and typed-contract requirements remain.

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


## Stage 45 — verify selected objective evidence at finalization

The native finalizer now accepts a selected single-basis or multi-basis winner
only when its objective-selection audit has the expected schema, explicitly
certifies training-only selection, and places the selected identity on the
recorded Pareto front. The selected objective evidence fingerprint must match
the corresponding unique evidence record. Finalization also rejects negative,
non-finite, boolean, or incorrectly typed error, variability, and complexity
values rather than coercing them into cross-family ranking inputs.

This closes the boundary between the two independently produced Pareto
families and the final cross-family comparison: a selected ID alone is no
longer sufficient to reach the frozen production model. Regression-test
source covers the stricter single- and multi-basis evidence contracts. Tests
have not been run; no CI, experiment, worker, benchmark, smoke workflow, or
provider call was launched.


## Stage 46 — require identifiable final training designs

Before cross-family comparison, finalization now constructs each selected
family winner's training design and requires full column rank, including the
intercept. A rank-deficient family winner is recorded as rejected and cannot
be promoted merely because its fold error is lower; the other independently
selected family remains eligible. If no family has an identifiable training
design, native finalization returns an explicit no-credible-candidate result.
The frozen-model verifier independently requires the finalized design-rank
audit to match the full coefficient dimension.

This is an identifiability check on the supplied training observations, not a
claim of global parameter identifiability or numerical stability outside the
observed training design. Regression-test source covers a collinear joint
basis that loses to an identifiable single-basis alternative. Tests have not
been run; no CI, experiment, worker, benchmark, smoke workflow, or provider
call was launched.


## Stage 52 — verify identifiability for every cross-family option

The frozen production verifier and worker artifact verifier now require each
serialized single-/multi-basis family option to carry a full-column-rank
training-design audit. The selected model's rank and condition-number record
must match the winning family option. This prevents a report from hiding a
rank-deficient alternative inside the cross-family comparison while claiming
only the final winner was identifiable.

Regression-test source covers rank-deficient family options at both
verification boundaries. Tests have not been run; no CI, experiment, worker,
benchmark, smoke workflow, or provider call was launched.


## Stage 47 — honor declared unary operators in native proposal generation

The bounded native template generator now emits unary-function proposals only
when the immutable problem contract explicitly declares a supported function.
The function allowlist matches the restricted expression parser; unknown
operator names are ignored rather than guessed or evaluated. Unary proposals
consume the same search-attempt and candidate budgets as binary templates,
remain deterministic under the declared seed, and do not inspect training
targets or evaluation data.

The default contract with no declared unary functions retains its previous
candidate sequence. Regression-test source covers explicit allowlisting,
unsupported names, deterministic order, and budget truncation. Tests have not
been run; no CI, experiment, worker, benchmark, smoke workflow, or provider
call was launched.


## Stage 48 — generate bounded square templates for declared exponentiation

The native generator now emits the bounded variable-to-the-second-power
structural template only when exponentiation (**) is explicitly declared in
the contract's binary-operator allowlist. Each square consumes one search
attempt and obeys the same candidate cap. Undeclared exponentiation, caret
notation, and unknown operators remain excluded. This adds a minimal nonlinear
polynomial basis without introducing arbitrary exponents or unrestricted
expression search.

Regression-test source covers explicit declaration and the unsupported-operator
case. Tests have not been run; no CI, experiment, worker, benchmark, smoke
workflow, or provider call was launched.


## Stage 49 — compose declared unary and binary templates

When both operator families are declared, native proposal generation now
also emits bounded unary applications over each admitted pairwise binary
template (for example, sin(x + y)). The inner binary expression is retained
as its own proposal, and the composed expression is a separate candidate.
Each generation consumes one attempt, preserving deterministic ordering and
the shared attempt/candidate limits. No undeclared function or operator is
introduced.

Regression-test source covers the combined operator path and budget order.
Tests have not been run; no CI, experiment, worker, benchmark, smoke workflow,
or provider call was launched.


## Stage 50 — validate candidate-generation limits without coercion

The public native template generator now rejects boolean, floating-point,
string, and negative limit values rather than coercing them into a candidate
cap. Declared unary and binary operator lists are deduplicated in stable
first-seen order before proposal attempts are charged, so repeated declarations
cannot consume the bounded search budget or suppress distinct templates.

Regression-test source covers strict limit types and duplicate operator
declarations. Tests have not been run; no CI, experiment, worker, benchmark,
smoke workflow, or provider call was launched.


## Stage 51 — use declared multiplication for self-product templates

When multiplication is declared but exponentiation is not, native proposal
generation now includes bounded self-products such as x*x. If exponentiation
is also declared, the generator prefers the explicit x**2 form and avoids
spending budget on the duplicate self-product. Each self-product consumes one
search attempt and remains subject to the candidate cap.

Regression-test source covers multiplication-only self-products. Tests have
not been run; no CI, experiment, worker, benchmark, smoke workflow, or provider
call was launched.


## Stage 53 — share the safe unary-function allowlist

The native template generator now imports the unary-function allowlist from
the restricted AST parser instead of maintaining a second copy. The parser
checks that its callable mapping and exported allowlist remain identical.
This prevents generator/parser drift: a generated function call is admitted
only when the exact same parser accepts that function name.

Regression-test source remains offline and exercises supported and
unsupported declarations. Tests have not been run; no CI, experiment, worker,
benchmark, smoke workflow, or provider call was launched.
