# Core-295 same-run ablation artifact contract

**Status:** adapter contract; not wired to a runner or workflow.  
**Branch:** `promotion/rerun-code-review`

## Why a Core-295 wrapper artifact is required

The current Core-15 aggregate reads legacy checkpoint dictionaries keyed by equation index, with nested condition objects. Its strict CI mode selects each downloaded artifact's own shard checkpoint and refuses committed-master backfill. However, those legacy checkpoints do not carry the Core-295 immutable run ID, catalogue hash, task-set hash, or stable equation IDs. They cannot independently prove same-run provenance for Core-295.

Core-295 therefore requires an explicit wrapper envelope. The adapter that writes it must preserve the native per-arm payload without treating legacy equation indices as Core-295 identities.

## Required JSON schema (contract version v1)

Each shard writes one JSON object:

```json
{
  "schema": "core295-ablation-shard-v1",
  "run_id": "copied from immutable task manifest",
  "catalogue_sha256": "copied from immutable task manifest",
  "task_set_sha256": "copied from immutable task manifest",
  "shard_id": 0,
  "shard_count": 100,
  "equations": [
    {
      "equation_id": "stable catalogue ID",
      "arms": {
        "pysr_only": {"status": "success", "payload": {}},
        "hypatia": {"status": "success", "payload": {}},
        "hypatia_nollm": {"status": "success", "payload": {}}
      }
    }
  ]
}
```

Allowed terminal statuses are `success`, `failed`, `timeout`, and `skipped`. Each arm must be represented explicitly, including failures. A missing arm is malformed/incomplete, not an implicit success. The payload is preserved by the producer; this verifier only checks its envelope and terminal status.

The three arm names are read from the current Core-15 ablation implementation. The runner currently enables the no-LLM arm by default in strict CI. Core-295 must keep all three enabled to preserve that contract.


## Native checkpoint envelope adapter

[\u0060core295_wrap_ablation_checkpoint.py\u0060](../scripts/core295_wrap_ablation_checkpoint.py) packages an already-produced native checkpoint into the versioned wrapper. It requires an explicit mapping JSON keyed by stable Core-295 equation ID. Each mapping value supplies the runner-local `checkpoint_key` and an explicit `arm_statuses` object containing all three arm statuses. The adapter verifies that mapping IDs exactly match the manifest shard, checkpoint keys are unique, and successful arms have native payload objects. It records SHA-256 hashes of the checkpoint and mapping as provenance and refuses to overwrite an existing artifact.

Example mapping shape:

\u0060\u0060\u0060json
{
  "CHEM-EQUATION-001": {
    "checkpoint_key": "0",
    "arm_statuses": {
      "pysr_only": "success",
      "hypatia": "success",
      "hypatia_nollm": "timeout"
    }
  }
}
\u0060\u0060\u0060

The mapping is an explicit assertion by the shard producer, not something inferred from the legacy checkpoint. In particular, do not map legacy Core-15 equation indices to Core-295 IDs by position or name similarity. A real Core-295 runner must supply the stable-ID mapping and arm statuses from its own execution ledger. This wrapper does not launch or adapt the current hard-coded Core-15 equation generator; that execution adapter remains unimplemented.

## Verifier

From repository root, after shard adapters have emitted the wrapper artifacts:

```bash
python scripts/core295_verify_shard_results.py \
  --manifest data/core295_plans/<run-id>.json \
  --shard-results data/core295_results/<run-id>/shard-*.json \
  --report-json data/core295_reports/<run-id>-coverage.json \
  --report-md data/core295_reports/<run-id>-coverage.md
```

Supply exactly one file per planned shard. The verifier checks manifest hashes and exact-once assignment; run/catalogue/task-set identity; unique and complete shard IDs; shard-to-equation assignment; unique equation rows; exactly the three required arms; and explicit terminal status for each arm. It rejects missing, extra, duplicate, malformed, stale, and cross-run artifacts. It never searches historical result folders and never backfills.

The verifier exits nonzero on structural/coverage failure. If coverage is complete but an arm has a non-success status, it writes a report with `all_arms_successful=false`; coverage verification is not equivalent to a successful benchmark.

## Important boundary

The verifier is not the Core-295 aggregate analysis stage. It does not merge native checkpoint payloads, calculate R² or statistical tests, select winners, or declare scientific success. Those computations require an explicit, separately reviewed result-payload schema and an adapter that preserves Core-15 analysis semantics. Do not wire this verifier into `run_all.sh` or GitHub Actions until the Core-295 shard adapter and payload mapping exist.

No scripts, tests, validators, experiments, or workflows were executed to create this contract.
