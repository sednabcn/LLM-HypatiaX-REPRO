# HybridSystem V60 migration boundary

## Status

V60 is introduced as a separate, opt-in implementation name in
`hypatiax/tools/symbolic/hybrid_system_v60.py`. The first increment is an
explicit compatibility adapter over `HybridDiscoverySystem` in
`hybrid_system_v50_2.py`; it is **not** the completed staged V60 architecture
and makes no claim of improved scientific performance.

The adapter preserves the existing constructor and public discovery entry
points. Its result includes `implementation_provenance` with:

- `engine_version: 6.0.0`
- `implementation_mode: v50_2_compatibility_adapter`
- `native_v60_pipeline: false`
- `compatibility_baseline: hybrid_system_v50_2`

This explicit marker prevents downstream reporting from mistaking the
compatibility bridge for native V60 execution.

## Selection

The reproducibility configuration keeps V50.2 as the default:

```yaml
engine:
  name: "hybrid_system_v50_2"
  version: "5.4"
  implementation: "v50_2"
```

Callers that deliberately opt in can set `engine.implementation: "v60"`
and construct through
`create_hybrid_discovery_system_from_config(config, ...)`. Direct callers may
use `create_hybrid_discovery_system("v60", ...)`. Unknown selectors fail
closed; the factory does not silently fall back.

This increment adds a version-selection API, not an automatic change to
existing experiment runners. Existing direct V50.2 imports continue to use
V50.2 until a runner explicitly adopts the factory.

## Planned native V60 stages

The compatibility boundary is intended to be replaced incrementally by
independently versioned components:

1. Typed problem-contract validation and immutable run context.
2. Candidate generation with bounded LLM/PySR producer adapters.
3. Candidate normalization, identity, deduplication, and lineage.
4. Hard scientific gates and separately recorded soft diagnostics.
5. Training-only fold evidence, residual diagnostics, and structure stability.
6. Pareto selection with independently verifiable objective evidence.
7. Frozen far-set evaluation after selection.
8. Versioned discovery report and worker-side integrity verification.

Each stage must retain candidate IDs, source provenance, rejection reasons,
budget accounting, and deterministic failure states. The far set must remain
inaccessible to selection and retry logic. Existing worker report contracts
and the Exp2 normalized extrapolation score remain compatibility requirements.

## Migration rules and limitations

- V50.2 remains the default and must not be modified merely to introduce V60.
- V60 is opt-in; no silent fallback from V60 to V50.2 is permitted.
- The adapter currently executes V50.2 behavior. It does not yet provide native
  V60 stage isolation, new selection semantics, or performance improvements.
- The implementation should be migrated stage-by-stage with offline regression
  source coverage and CI verification. No benchmark or scientific improvement
  claim is valid until explicitly authorized evaluation provides evidence.
- Do not launch experiments, workers, benchmarks, smoke workflows, or live LLM
  calls as part of architecture implementation.
