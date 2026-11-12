# Core-295 deterministic task planner

The task planner converts a fully accepted and frozen Core-295 catalogue into an immutable, deterministic task manifest. It is a planning utility only; it does not run scientific work.

## Usage

From the repository root:

```bash
python scripts/core295_plan_tasks.py \
  --catalogue config/core295_catalogue.json \
  --shards 100 \
  --run-id core295-review-run-001 \
  --output data/core295_plans/core295-review-run-001.json
```

The output path must not already exist. The caller supplies a stable run label. The planner creates parent directories but will not overwrite an existing manifest.

## Fail-closed acceptance requirements

The planner requires:

- Catalogue status `ready`, target count 295 and per-domain target 59.
- Frozen sampling frame with source universe, inclusion/exclusion rules, selection method, statistical-unit definition and source-family definition.
- Exactly 295 entries, all with status `accepted`.
- Exactly 59 accepted entries in each of Chemistry, Biology, Physics, DeFi AMM and DeFi Risk.
- Unique equation IDs and structural fingerprints.
- Registered source references with domain-compatible source records.
- Reviewer/date, documented E4 structural-equivalence classification and rationale.
- Source-family and independence-unit IDs, with 295 unique independence-unit IDs.
- Non-empty variables and matching train/extrapolation ranges for every variable.
- A ready deterministic generator contract (method, seed policy and parameter sampling).

These checks validate the catalogue's declared fields and internal consistency. They do not independently establish scientific correctness, source transcription fidelity, algebraic inequivalence or actual statistical independence. Those remain review responsibilities.

## Manifest contract

The JSON manifest contains the catalogue SHA-256, canonical task-set SHA-256, shard-plan SHA-256, sorted stable equation IDs, domain labels, source-family and independence-unit IDs, and per-shard equation lists. Assignment is deterministic round-robin over domain-ordered, equation-ID-sorted tasks. An internal exact-once check ensures every task appears in one shard and only one shard.

The manifest is tied to the exact catalogue bytes. Any catalogue edit changes the catalogue hash and requires a new plan. The run label is descriptive; it is not proof of an executed GitHub Actions run.

## Safety boundary

No data generation, model calls, solver invocation, Julia startup, workflow dispatch, experiment execution, catalogue mutation, equation acceptance or result aggregation occurs. The planner is not run as part of this change. A successful plan would mean only that the static catalogue contract passed and a deterministic task manifest was written; it would not authorize a scientific run.
