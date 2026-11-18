# HybridDiscoverySystem Exp2 integration audit and remediation

**Status:** integration PR in progress  
**Audit baseline:** PR #217 merge commit `4d8f8e1be25a51745fb07fc86175ebbe2a216308`  
**Target integration branch:** `master`  
**Scope:** source/documentation integration only; no experiment, worker, benchmark, LLM, local test, or CI execution.

## Executive summary

The HybridDiscovery feature stack contains typed scientific contracts, candidate validation, training-only fold evaluation, Pareto selection, nested-structure evidence, runtime budgets, and strict serialized-report validation. Before this remediation, the normal Exp2 adapter did not always provide a typed `DiscoveryProblem`, the adapter dropped the discovery report when converting the subprocess result into a `MethodResult`, and the worker accepted missing reports.

This change set addresses those three integration gaps:

1. The standard Exp2 HybridDiscovery adapter now constructs a JSON-safe `discovery_problem_spec` for every invocation, unless the caller supplies one explicitly.
2. Only declared units, variable domains, target units, and `discovery_constraints` are passed through. The adapter does not infer physical facts from variable names. Reserved variable names are mapped consistently for the contract boundary.
3. The subprocess continues to deserialize and validate the typed contract before discovery. The resulting contract audit, `DiscoveryReport`, and training-only selection summary are retained in the `MethodResult` metadata.
4. The Exp2 worker now requires a report and an active typed-contract audit for every expected `HybridDiscoverySystem v50_2 (tools)` equation row. A missing report is a worker validation failure rather than a successful zero-report artifact.

## Important scientific qualification

Activating a typed contract is not equivalent to supplying complete physical knowledge. If a protocol does not declare units, variable domains, or physical constraints, those fields remain absent/empty. No dimensional or domain claim is made in that case. The candidate validator can still apply its symbolic checks and any declared gates, but the report must not be interpreted as proof of physical validity.

Protocols should progressively add authoritative declarations:

- `target_unit`
- `variable_units`, keyed by protocol variable name
- `variable_domains`, keyed by protocol variable name
- `discovery_constraints`, using the versioned `ConstraintSpec` schema

Unknown or incomplete declared hard-constraint evidence remains fail-closed in the candidate-validation layer.

## End-to-end path after this change

1. The protocol runner supplies equation metadata, feature names, training arrays, and the HybridDiscovery method configuration.
2. `HybridSystemV50_2Method.run()` creates or accepts `discovery_problem_spec`. It maps only declared per-variable metadata to the sanitized variable names used by the isolated PySR subprocess.
3. `_SUBPROCESS_WORKER` deserializes the spec through `discovery_problem_from_dict()`, verifies exact variable-name alignment, computes the canonical contract digest, and attaches the typed object to discovery metadata.
4. `HybridDiscoverySystem.discover()` activates the typed budget runtime, candidate scientific gates, and training-only search-validation/Pareto path.
5. The subprocess returns the discovery report and contract provenance. The parent adapter preserves both in `MethodResult.metadata`.
6. The worker validates the report schema and Pareto evidence, and requires one report per expected HybridDiscovery equation row before declaring the worker output complete.
7. Far-region evaluation remains downstream of candidate selection. The report contract continues to state that far evaluation was not used for selection.

## Worker acceptance rules

For each expected method/equation row whose method name is exactly `HybridDiscoverySystem v50_2 (tools)`:

- `metadata.discovery_report` must be present and pass the existing strict report-contract validator.
- `metadata.discovery_problem_contract.active` must be exactly `true`.
- The report's `far_evaluation_used_for_selection` must remain exactly `false`.
- The number of validated HybridDiscovery reports must equal the number of expected HybridDiscovery rows.

A report with a legitimate failure status (for example, `no_credible_candidate`) is still an auditable report. The worker's job is to reject missing or malformed evidence, not to force an equation to be accepted.

## Remaining follow-up work (not silently claimed as solved)

### Candidate provenance and diversity

The current inner LLM/PySR engine can choose a single best result before the outer candidate-level Pareto stage sees it. Some paths can therefore fail to preserve LLM proposals and PySR alternatives as distinct candidate records. The candidate-validation call in the retry loop also currently labels the source as `pysr_search`; source attribution should be derived from the actual result path (for example, `llm_proposal` for an LLM-only candidate).

These are follow-up algorithm changes, not part of the P0–P2 integration patch.

### Early stopping and candidate coverage

Training-`R^2` early stopping can reduce the candidate pool available to Pareto selection. A future change should make stopping policy aware of the minimum candidate evidence required, or explicitly record that the Pareto comparison was performed on a restricted pool.

### Physical completeness and uncertainty

The typed contract does not invent missing physical declarations. Coarse deterministic domain grids are evidence, not global proofs. Expression-string recurrence is not algebraic equivalence. A calibrated predictive-uncertainty estimate is not yet established by this integration change.

### Verification still required

No tests or CI were run as part of this source change. After review and merge, the user-controlled verification sequence should include:

1. Offline contract construction/deserialization and reserved-name mapping regression tests.
2. Worker tests for missing report, inactive contract, malformed report, and exact expected coverage.
3. A controlled Exp2 worker run with reports for every HybridDiscovery equation.
4. Known-equation recovery, physical-rejection, LLM-unavailable fallback, and reproducibility evidence.

No experiment, worker, benchmark, smoke workflow, or LLM API call is started by this PR.
