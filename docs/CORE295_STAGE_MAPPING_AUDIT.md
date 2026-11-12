# Core-295 stage mapping audit

**Status:** mapping verified against the current Core-15 runner; Core-295 implementation remains pending.  
**Branch:** `promotion/rerun-code-review`

## Verified Core-15 sequence

The root `run_all.sh` step registry orders the relevant stages as:

1. `exp1_ablation`
2. `exp1_ablation_aggregate`
3. `exp1_five`

The runner implementation confirms three different contracts:

- `exp1_ablation` invokes `hypatiax/experiments/benchmarks/exp1_ablation.py` with the PySR-only, HypatiaX, and optional no-LLM arms. Its CI shard inputs select the work assigned to a shard.
- `exp1_ablation_aggregate` merges the per-shard checkpoint files, checks equation and arm completeness, and produces aggregate ablation outputs. In strict artifact mode it uses the current run's shard artifacts rather than silently filling gaps from a historical master checkpoint.
- `exp1_five` invokes `hypatiax/experiments/benchmarks/exp1_five_system.py` and writes a separate five-system result family.

## Mapping decision

| Core-295 ID | Core-15 counterpart | Contract to preserve |
|---|---|---|
| `exp295_ablation` | `exp1_ablation` | Execute the three ablation arms over the Core-295 equation task set |
| `exp295` | `exp1_ablation_aggregate` | Merge same-run shard artifacts; enforce exact equation/arm coverage; aggregate ablation analysis |
| `exp295b` | `exp1_five` | Run the separate five-system comparison over the Core-295 equation task set |

The mapping follows the existing Core-15 stage order. In particular, `exp295` is the aggregate stage; it is not a second model-comparison experiment. `exp295b` is the five-system comparison.

## Current implementation gap

A static inspection of the current branch found:

- `run_all.sh` does not register any of the three Core-295 IDs in `_STEP_ORDER`.
- `.github/workflows/ci_runner_repro.yml` does not offer the Core-295 IDs in its single-experiment dispatch choices or multi-dispatch allowlist.
- `ci_runner/run_fresh_experiments.sh` currently includes the Core-15 stages, not Core-295 stages.
- No `exp295.py` or `exp295b.py` script exists at the repository root `scripts/` path checked during this audit. The intended implementation should reuse the verified Core-15 architecture through explicit Core-295 catalogue adapters, not invent duplicate model implementations.

Therefore this document resolves **stage correspondence only**. It does not claim the Core-295 stages are implemented, runnable, or authorized.

## Required implementation contracts

### `exp295_ablation`

- Read only accepted catalogue entries from a frozen catalogue snapshot.
- Use stable equation IDs as task identities; never rely on list indices alone.
- Preserve Core-15 method arms, model settings, metrics, data split, seed policy, and per-equation timeouts unless a separately reviewed protocol change says otherwise.
- Use a dedicated Core-295 results/checkpoint namespace.
- Support deterministic domain-balanced shard assignment and exact-once task coverage.
- Record catalogue hash, task-set hash, code commit, protocol hash, seed, shard ID/count, and runtime settings in provenance.

### `exp295` (aggregate)

- Consume only artifacts tagged with the same run ID, catalogue hash, protocol hash, and task-set hash.
- Reject stale, duplicate, missing, unexpected, malformed, or cross-run shard artifacts.
- Require all expected equation IDs and all expected ablation arms.
- Do not backfill missing current-run tasks from committed or historical checkpoints in strict mode.
- Emit a machine-readable coverage manifest and aggregate outputs.

### `exp295b` (five-system)

- Preserve the distinct five-system comparison contract of `exp1_five_system.py`; do not describe it as the ablation aggregate or as identical to the ablation arms.
- Consume the same frozen Core-295 task set and dedicated result namespace.
- Record per-equation status and require exact expected coverage before declaring completion.
- Preserve and disclose known differences between current five-system implementation and manuscript descriptions; this mapping does not repair those differences.

## Static workflow requirements before any dispatch

- Add the three IDs to the workflow choice list and multi-dispatch allowlist only after all three runner stages exist.
- Add Core-295-specific shard policy without changing Core-15's five-domain shard behavior.
- Preserve per-job model workers, Julia threads, PySR population, and timeouts.
- Ensure aggregate runs after all shard artifacts are available and has a strict same-run artifact contract.
- Add offline tests for ID planning, domain balancing, exact-once assignment, stale checkpoint rejection, aggregation, and 295/295 plus 59/domain completeness.
- Keep the fresh-rerun workflow separately gated by its explicit authorization input; do not add Core-295 to it until its own protocol and readiness gates pass.

## Verification boundary

This audit was based on repository file contents and workflow definitions. It did not run `run_all.sh`, any Python stage, tests, validators, GitHub Actions, experiments, or live APIs. No Core-295 stage has been dispatched. The stage mapping is a code-structure finding, not scientific acceptance or experiment evidence.
