# Tau calibration provenance-chain audit

**Status:** offline design audit; no calibration, evaluation, formula generation, provider call, or experiment was run.

## Scope

This audit compares the provenance fields currently checked by:

- `scripts/validate_tau_calibration_manifest.py`
- `scripts/validate_tau_independent_evaluation.py`
- `scripts/evaluate_tau_convergence.py`

It is deliberately a gap analysis, not a claim that existing hashes or review gates are useless. The validators enforce important structural controls: full-length commit-ID syntax, SHA-256 syntax, pinned evaluator-version strings, family-ID separation, formula-hash uniqueness, and human adjudication evidence. Those controls improve traceability and prevent several classes of accidental reuse.

## Findings

### 1. Commit identifiers are format-checked, not resolved

The calibration and independent-evaluation validators require 40-character SHA-1 or 64-character SHA-256-looking Git object IDs. They do not query Git or otherwise establish that an identifier:

- resolves to a commit object in the intended repository;
- is reachable from an approved repository/ref;
- contains the source files actually used by the run; or
- was the checkout from which the outcomes were produced.

A well-formed but nonexistent, unrelated, or mistyped object ID can therefore pass the current format gate.

### 2. Evaluator versions are labels, not implementation identities

The independent-evaluation validator pins `tau-independent-evaluation-validator-v1`, and the convergence evaluator emits `tau-convergence-evaluator-v1`. A version string is useful for schema compatibility, but it is not cryptographically bound to the source implementation. The same label could remain in place after code changes, or be copied into a payload produced by another implementation.

Neither validator currently requires a digest of the evaluator source or a packaged evaluator artifact.

### 3. Data hashes are opaque declarations

The calibration manifest requires SHA-256-shaped values for the calibration manifest and each source, formula, and training-row payload. The independent-evaluation payload similarly requires hashes for the evaluation manifest, calibration manifest, historical-74 registry, and each row's source, formula, and training rows.

The validators check the shape and (for formulas) uniqueness of these strings. They do not receive the corresponding bytes or artifact paths, so they cannot recompute the digests or prove that a row's values came from the declared source/training data. A syntactically valid hash is not evidence that the hashed object was retained or that the correct object was hashed.

### 4. Generated reports do not preserve a complete input-to-output attestation

The independent-evaluation report includes the evaluator version and risk result, but does not echo a complete provenance envelope binding the report to the exact input payload, calibration/evaluation manifests, source revisions, and evaluator implementation.

The convergence report includes its evaluator version and protocol/results, but does not include an input-payload digest or a source-revision/evaluator-artifact digest. This makes later report verification dependent on external records.

### 5. Human adjudication remains a separate evidence boundary

Family review references and independence justifications are required, but their contents are not resolved or checked by these scripts. That is intentional: mathematical independence cannot be proven by a hash or a non-empty string. The audit record itself must remain available, versioned, and tied to the exact candidate/formula reviewed.

## Recommended provenance contract before any real calibration

Do not retrofit unverifiable claims into historical records. For a future, newly frozen calibration/evaluation package, define a versioned provenance envelope with these components:

1. **Repository identity:** canonical repository URL/name and full commit ID; a verifier must resolve the commit and confirm the expected repository identity. Record the working-tree cleanliness state and reject dirty/untracked source state for production outcomes.
2. **Implementation identity:** SHA-256 of the exact evaluator source file(s), plus an explicit schema/version identifier. Prefer a reproducible source bundle or immutable artifact digest when more than one file contributes to evaluation.
3. **Input identity:** hash the exact bytes of each frozen manifest, source registry, formula serialization, training-row dataset, and outcome input. Store the artifact itself or a durable immutable locator alongside the digest.
4. **Execution identity:** record interpreter/runtime version, dependency lockfile digest, command/arguments, and relevant deterministic settings. Do not include secrets or credentials.
5. **Output identity:** write a report envelope containing the input digest, manifest digests, source commit(s), evaluator source/artifact digest, protocol version, and output digest. A separate verifier should recompute digests from retained artifacts.
6. **Human-review identity:** reference a versioned review artifact by immutable commit/path and digest; record reviewer role and review date. Keep the substantive family-boundary rationale, not just a status token.

The verifier should distinguish:
- **format-valid:** fields have valid shapes;
- **reference-resolved:** commits and immutable artifact locators resolve;
- **digest-verified:** recomputed bytes match declared hashes;
- **execution-attested:** the recorded runtime and implementation are tied to the output;
- **scientifically adjudicated:** human family review is complete.

Passing one level must not imply the next. In particular, a provenance verifier cannot establish mathematical independence.

## Safe implementation sequence

1. Agree on the provenance-envelope schema and artifact-retention policy before changing validator inputs.
2. Add pure offline digest and schema tests using temporary fixture files; test altered bytes, missing artifacts, wrong repository identity, nonexistent commits, dirty-tree declarations, and evaluator-source drift.
3. Add a report-envelope verifier that independently recomputes hashes. Keep the existing risk tests unchanged.
4. Only then version the calibration/evaluation input schemas and migrate future records. Do not silently reinterpret historical payloads.
5. Require the provenance verifier and the existing R², workflow-contract, and regression gates before any separately authorized expensive run.

## Explicit non-claims

This audit does not establish that any current hash is wrong, that a past result was fabricated, or that any current cohort is ready. It does not create family IDs, populate calibration/evaluation records, select tau, change routing, or authorize experiments. The current fail-closed `degradation_tau: null` policy remains appropriate until the cohort and provenance gates are satisfied.
