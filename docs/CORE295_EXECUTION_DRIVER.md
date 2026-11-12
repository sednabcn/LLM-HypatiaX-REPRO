# Core-295 shard execution driver

**Status:** fail-closed adapter harness. Domain-specific scientific adapters are not yet implemented.  
**Branch:** `promotion/rerun-code-review`

## Driver boundary

`scripts/core295_run_shard.py` owns the orchestration boundary for one planned shard:

1. Requires the exact catalogue bytes hashed into the task manifest.
2. Requires a frozen, ready 295-entry catalogue: 59 accepted equations per domain, complete generator declarations and non-null train/extrapolation ranges.
3. Validates task-set and shard-plan hashes, exact-once shard assignment, and task/catalogue identity.
4. Requires one trusted adapter callable for every domain present in that shard.
5. Supplies the full accepted entry, run/shard identity, required three-arm list, and deterministic seed material derived from run ID, equation ID, and the entry's declared seed-policy string.
6. Requires an explicit terminal status and payload for every arm, then writes the same-run `core295-ablation-shard-v1` envelope without overwriting an existing artifact.

The driver does not interpret formula strings as executable code. It does not guess a generator from a formula, reuse Core-15 equation indices, or infer success from a missing result.

## Adapter interface

A trusted adapter is a Python callable exposed as `module.path:function_name`. It is invoked once per equation:

```python
def run_equation(*, entry: dict, context: dict) -> dict:
    # Generate data according to entry["generator"] and entry["input_ranges"].
    # Run all requested arms using the frozen benchmark contract.
    # Return exactly the three keys below, each with explicit status.
    return {
        "pysr_only": {"status": "success", "payload": {"...": "..."}},
        "hypatia": {"status": "success", "payload": {"...": "..."}},
        "hypatia_nollm": {"status": "success", "payload": {"...": "..."}},
    }
```

The adapter must consume `context["seed_material_sha256"]` according to the declared seed policy, and must respect `context["allow_live_services"]`. A successful status requires a JSON object payload. Non-success statuses must be explicit (`failed`, `timeout`, or `skipped`); they are not converted to successful results. The driver stops on adapter exceptions or malformed output rather than writing a partial shard artifact.

Adapters are executable code and must be reviewed/trusted before use. This interface does not itself guarantee that their data generation, model settings, or outputs are scientifically valid.

## Invocation (only after prerequisites and authorization)

```bash
python scripts/core295_run_shard.py \
  --manifest data/core295_plans/<run-id>.json \
  --catalogue config/core295_catalogue.json \
  --shard-id 0 \
  --adapter 'Chemistry=project.adapters.chemistry:run_equation' \
  --adapter 'Biology=project.adapters.biology:run_equation' \
  --output data/core295_results/<run-id>/shard-000.json \
  --execute
```

Include adapters only for domains represented in the shard, and exactly one per represented domain. Add `--allow-live-services` only when live external services have been explicitly authorized. Without `--execute`, the driver exits blocked and does not import adapters or invoke models.

## Current blockers

The current canonical catalogue is still draft, not ready; entries are proposed, generator statuses are pending, sampling frame is not frozen, and numerical input ranges are unset. Thus the existing task planner cannot produce a valid execution manifest from the current catalogue, and this driver will refuse to execute it.

No domain adapters currently exist under this contract. They must be implemented and reviewed against the Core-15 method/configuration freeze, including generator semantics, model arm parity, seed policy, timeouts, and payload fields. In particular, do not simply import the Core-15 benchmark module: it hard-codes Core-15 equations and would not run the 295 catalogue entries.

The driver is not wired to `run_all.sh` or GitHub Actions. The three-stage aggregate/five-system contracts remain separate work. The shard wrapper helper remains useful for externally produced native checkpoints, but should not be used to manufacture Core-295 identities from Core-15 checkpoint positions.

## Safety and validation status

The driver has an explicit `--execute` gate, refuses output overwrite, performs no catalogue mutation, and writes only a complete shard envelope after every planned equation has returned all three arms. It does not accept equations or compute aggregate statistics.

This file and driver were committed as source changes only. No Python code, tests, validators, models, APIs, experiments, or workflows were executed.
