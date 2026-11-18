# HybridSystem V60 migration boundary

## Status

V60 remains opt-in. It now performs typed problem-contract preflight, captures
an immutable data-free run context, and generates a bounded, deterministic
pool of algebraic template proposals in
`hypatiax/tools/symbolic/v60_candidate_generation.py`. Candidate fitting,
LLM/PySR production, normalization, scientific gates, validation, and
selection still use the V50.2 compatibility baseline. The template pool is
reported as generation evidence; it is not yet the selected/fit candidate pool.
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
Malformed or misaligned explicit contracts fail closed. Calls without a
typed contract retain the compatibility path.

Result `implementation_provenance` records:
- `engine_version: 6.0.0`
- `implementation_mode: native_contract_preflight_v50_2_discovery`
- `native_v60_pipeline: false`
- `native_v60_stages`: typed contract/run context plus bounded data-independent template generation
- `native_v60_candidate_proposals`: generated proposal records with deterministic IDs, source, strategy, and seed
- Candidate count and IDs in implementation provenance
- `native_v60_contract_preflight` and the data-free `v60_run_context`
- `compatibility_baseline: hybrid_system_v50_2`

## Selection

The reproducibility configuration keeps V50.2 as the default. Callers may
select V60 explicitly with `engine.implementation: "v60"` through the factory
or the Exp2 benchmark runner selector. Unknown selectors fail closed.

## Remaining native V60 stages

1. Bounded candidate generation with LLM/PySR producer adapters.
2. Candidate normalization, identity, deduplication, and lineage.
3. Hard scientific gates and separately recorded soft diagnostics.
4. Training-only fold evidence, residual diagnostics, and structure stability.
5. Pareto selection with independently verifiable objective evidence.
6. Frozen far-set evaluation after selection.
7. Versioned discovery report and worker-side integrity verification.

Each stage must retain candidate IDs, source provenance, rejection reasons,
budget accounting, and deterministic failure states. The far set must remain
inaccessible to selection and retry logic. Existing worker report contracts
and the Exp2 normalized extrapolation score remain compatibility requirements.

## Migration rules and limitations

- V50.2 remains the default and is not modified by this stage.
- V60 is opt-in; no silent selector fallback is permitted.
- V60 currently owns only contract preflight/run-context capture. Discovery
  behavior after preflight remains V50.2.
- No benchmark or scientific improvement claim is valid until explicitly
  authorized evaluation provides evidence.
- Do not launch experiments, workers, benchmarks, smoke workflows, or live
  LLM calls as part of architecture implementation.
