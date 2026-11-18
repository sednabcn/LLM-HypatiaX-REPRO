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
- `implementation_mode: native_contract_generation_normalization_fit_gates_training_validation_residual_stability_objective_selection_v50_2_final_evaluation`
- `native_v60_pipeline: false`
- `native_v60_stages`: contract/run context, bounded template generation,
  expression normalization, semantic identity, deduplication, lineage,
  declared scientific gates, bounded training-only affine fitting and
  bounded joint multi-basis fitting and fold-local joint refit validation,
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

`evaluate_selected_native_candidate_on_far_set()` is a separate, explicit
post-selection API in `v60_frozen_far_evaluation.py`. It requires a completed
training-only selection audit and verifies the selected candidate ID,
expression, and objective-evidence fingerprint before reading the far arrays.
It refits only that frozen expression on all training rows, then computes far
RMSE, NRMSE normalized by the training-target standard deviation, MAE, bias,
and R². The evaluator fingerprints the selection snapshot and far-set arrays.
It does not rank candidates, retry, update the selection audit, or return any
far metric to discovery/selection. It is not called by `discover()` and no far
arrays are added to `DiscoveryProblem` or the selector interface.

## Bounded external producer ingestion

Typed-contract calls may provide completed external proposals in
`metadata["v60_external_candidate_proposals"]`, with `llm_proposals`,
`pysr_proposals`, and explicit usage counters (`llm_call_count`,
`llm_token_count`, `pysr_search_attempt_count`). The ingestion boundary checks
source attribution, expression/strategy/seed types, and declared LLM/PySR
budgets, then applies a shared candidate/search-attempt ceiling before common
normalization and scientific gates. It records rejected proposals and budget
truncation. This is an adapter boundary only: it does not invoke providers,
load credentials, or perform LLM/PySR searches. The caller is responsible for
accurately reporting upstream usage. External proposal expressions pass
through the same restricted parser, semantic deduplication, hard gates,
training-only validation, and evidence-based selection as native templates.

## Native joint multi-basis fitting

The native pool also receives a bounded joint additive fit over groups of two
or three normalized basis candidates. For each group, all basis functions are
evaluated across every supplied training row and their coefficients plus an
intercept are estimated together by deterministic least squares. Group IDs are
stable hashes of the ordered basis candidate IDs; each record preserves the
basis IDs, expressions, coefficients, producer lineage, design rank, condition
number, training RMSE/NRMSE/R², and rejection reason where applicable. Group
attempts are bounded by the shared candidate/search budget and optional wall
clock budget. Non-finite or misaligned basis values reject the whole group;
rows are never silently dropped. This is a separate audit-only fitting stage:
its metrics do not influence the single-basis selector, do not rank groups,
and are not passed to V50.2. It has no far/evaluation-data input.

Joint basis groups now receive a separate bounded fold-validation audit. For
each fitted group, the validator verifies the stable group ID and exact
candidate-ID/expression lineage against the normalized proposal pool, then
evaluates every basis over the training rows. In each fold it independently
refits all basis coefficients and the intercept using only that fold's
training rows, and scores only the held-out rows. The audit preserves fold
row indices, fold-local coefficients, rank/condition diagnostics, RMSE/NRMSE/R²,
split protocol, and group-level budget/rejection accounting. It rejects
non-finite data, invalid basis outputs, mismatched lineage, and folds with too
few training rows; no rows are silently dropped. The validator has no far-set
argument and always reports `selection_performed: false`. This evidence is
not yet accepted by the single-basis objective selector or discovery-report
candidate schema. A separate evidence verifier now reconstructs every fold's
joint least-squares coefficients, held-out predictions, RMSE/NRMSE/R², rank,
condition number, and aggregate metrics directly from the supplied training
arrays. It checks fold row-index integrity, basis expression identity, producer
lineage, and the validation audit's far-data exclusion declaration. Verified
group evidence receives a canonical SHA-256 fingerprint. Tampered, incomplete,
or non-reproducible groups fail closed. Verification remains audit-only:
`selection_performed` is false, no far/evaluation arrays are accepted, and
groups remain ineligible for selection until a dedicated group-level
objective-selection contract is added.

Each stage must retain candidate IDs, source provenance, rejection reasons,
budget accounting, and deterministic failure states. The far set must remain
inaccessible to selection and retry logic. Existing worker report contracts
and the Exp2 normalized extrapolation score remain compatibility requirements.

## Migration rules and limitations

- V50.2 remains the default and is not modified by this stage.
- V60 is opt-in; no silent selector fallback is permitted.
- V60 currently owns contract preflight, bounded template generation,
  normalization/lineage, declared scientific gates, training-only affine and
  joint multi-basis fitting and fold-local joint refit validation, single-basis
  refit cross-validation, and independently recomputed training-evidence
  Pareto selection. V50.2 still performs production discovery and final
  evaluation; V60 selection is opt-in and remains isolated from far data.
- Candidate IDs identify canonical symbolic expressions; producer lineage is
  stored separately so deduplication never erases source attribution.
- No benchmark or scientific improvement claim is valid until explicitly
  authorized evaluation provides evidence.
- Do not launch experiments, workers, benchmarks, smoke workflows, or live
  LLM calls as part of architecture implementation.


The frozen evaluator is deliberately opt-in and separate from the discovery
call. Callers must invoke it only after selection has completed and must keep
its output downstream of all selection and retry decisions. Its report marks
selection and candidate ranking as not performed and records
`far_or_evaluation_data_used_for_selection: false`.


## Versioned discovery reports and worker integrity

Typed-contract V60 results now include `discovery_report_envelope`, built from
the native candidate pool, declared-gate audit, training-fold validation, and
training-only objective-selection audit. The report is explicitly marked
provisional: it describes the isolated native selection and does not replace
or promote the V50.2 production result.

The envelope uses schema `v60_discovery_report_envelope_v1` and contains a
canonical SHA-256 integrity digest over the complete versioned report payload.
Workers should call `verify_discovery_report_envelope()` before consuming the
report. Verification rejects unsupported schemas, missing or unknown fields,
tampered payloads, duplicate candidate IDs, invalid selected/Pareto references,
and any indication that far-evaluation evidence influenced selection.
`seal_discovery_report()` is available for trusted report producers. The
far-evaluation section remains a separate report field and is empty at
discovery time; post-selection evaluation must not mutate selection evidence.


The result provenance includes `native_v60_external_producer_audit`, including
reported usage, producer-call status, accepted/rejected counts, and budget
truncation. The audit explicitly records `producer_calls_performed: false`.


## Verified native joint multi-basis selection

Joint basis groups now have a dedicated objective selector in
`v60_multi_basis_objective_selection.py`. It is intentionally separate from
the single-basis selector and consumes only normalized proposals, completed
candidate-level hard-gate outcomes, the bounded joint-fit audit, the
joint-fold validation audit, and the independent verifier's output. It accepts
no training arrays and no far/evaluation arrays.

A group is eligible only when its fit and validation records are complete,
every basis candidate passed its completed hard gates, the candidate IDs and
normalized expressions match across all stages, producer lineage matches, and
the verifier marked every fold as verified. The selector reconstructs the
verifier's canonical SHA-256 payload and rejects mismatched fingerprints,
altered fold rows/metrics, missing groups, or incomplete evidence. Fold row
indices must be actual integers (booleans and floats are rejected).

The three minimized Pareto objectives are:
- mean fold NRMSE when every eligible group has defined NRMSE; otherwise mean
  fold RMSE is used consistently for the entire eligible pool;
- the corresponding population standard deviation across fold errors;
- symbolic complexity, defined as the sum of SymPy operator counts in each
  basis expression plus one additive-model term per basis (including the
  intercept).

Pareto membership uses componentwise dominance; deterministic tie-breaking
orders by primary error, symbolic complexity, error variability, then stable
group ID. The result records each group's verified-evidence fingerprint,
objective evidence, Pareto group IDs, and selected ordered basis IDs and
expressions. It reports `selection_performed: true` only for a completed
selection or an explicit no-credible-candidate decision. It never changes or
overrides the existing single-basis selected candidate and is exposed
separately as `native_v60_multi_basis_selection_audit`. This stage remains
opt-in/audit provenance and does not make V60 the production discovery path.


## Joint multi-basis selection in reports and worker contracts

Typed-contract V60 reports now embed the distinct group-selection audit at
`provenance.native_multi_basis_selection`. The existing report schema,
single-basis `selected_candidate_id`, and single-basis Pareto references remain
unchanged. Joint-group selection is supplemental provenance and never
replaces or overrides the single-basis result or V50.2 compatibility result.
The outer report-envelope SHA-256 covers this complete audit.

Worker verification reconstructs the embedded group-selection decision:
it validates the schema and far-data exclusion, objective-record digests,
and the embedded verified-fold snapshot against its independent evidence
fingerprint. It recomputes symbolic complexity from restricted expressions,
checks that objective metrics match the verified fold aggregates, derives the
pool-wide NRMSE-versus-RMSE objective consistently, and rebuilds the complete
componentwise-minimization Pareto frontier and deterministic tie-break. The
serialized Pareto order and selected group/basis references must exactly match
that reconstruction. Inconsistent evidence rejects the report even if both
the outer envelope and an objective-record digest are recomputed. A
no-credible-candidate decision remains explicit; a stage failure is marked
incomplete and cannot claim selection. Workers keep group selection in its
separate namespace from single-basis selection.



## Worker reconstruction of joint multi-basis selection

Each joint-basis objective record carries the independently verified fold
snapshot and its context (training row count, variable names, split strategy,
and recomputed fold metrics/coefficients). The worker recomputes the snapshot
fingerprint rather than treating a 64-character digest as proof. It then
reconstructs the error and variability objective from verified aggregates,
recomputes symbolic complexity from the restricted parser, validates objective
directions, derives the exact Pareto frontier, and applies the selector's
deterministic tie-break tuple: primary error, symbolic complexity, variability,
then stable group ID. A report is rejected if the frontier membership/order or
selected group differs. This is report-integrity verification only: it does
not invoke data providers, rerun discovery, or evaluate the far set.
