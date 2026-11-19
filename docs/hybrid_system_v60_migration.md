# HybridSystem V60 migration boundary

## Status

V60 remains opt-in. It now performs typed problem-contract preflight,
captures an immutable data-free run context, generates a bounded deterministic
pool of algebraic templates, and normalizes that pool using the restricted
symbolic-expression parser. Normalization creates stable semantic candidate
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
- Does not inspect targets, training residuals, validation folds, or far data.

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
- `native_v60_contract_preflight` and the data-free `v60_run_context`
- `compatibility_baseline: hybrid_system_v50_2`

## Selection

The reproducibility configuration keeps V50.2 as the default. Callers may
select V60 explicitly with `engine.implementation: "v60"` through the factory
or the Exp2 benchmark runner selector. Unknown selectors fail closed.

## Remaining native V60 stages

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
