# Core-295 final readiness report

Use `scripts/core295_final_readiness_report.py` to consolidate the current catalogue, tau-calibration manifest, source pipeline artifacts, workflow wiring, and design-policy state into one read-only report.

## Usage

From the repository root:

```bash
python scripts/core295_final_readiness_report.py
python scripts/core295_final_readiness_report.py --output-md data/core295_final_readiness.md --output-json data/core295_final_readiness.json
```

The output files are created exclusively; choose new paths or move prior reports before regenerating. Paths can be overridden for alternate review snapshots. The command returns 0 only for `READY_FOR_AUTHORIZED_RERUN`; otherwise it returns 1 and prints/writes the blockers.

## Gate coverage

- Catalogue total and per-domain counts; accepted status; duplicate equation IDs/fingerprints; registered source/domain compatibility; accepted-row reviewer, E4 rationale, source-family and independence-unit fields.
- Sampling-frame freeze status and required source-universe, selection, inclusion/exclusion, source-family and independent-unit declarations.
- Tau manifest status, predeclared calibration records/categories/grid, independence/edge definitions, hashes, evaluator and code provenance.
- Counts of discovery leads, OA provenance rows, extracted equation leads, review packets and staged records, including malformed JSONL.
- Static workflow text checks for dispatch, Core-295 stage identifiers, shard input and Julia thread configuration.
- Explicit visibility of the unresolved `exp295b` stage and `exp295` method-contract mapping.

## Interpretation and safety

The report is deliberately fail-closed. Missing or incomplete evidence prevents readiness. It does not accept or promote equations, execute the existing validators, verify scientific claims, establish algebraic inequivalence or statistical independence, validate legal rights, inspect GitHub Actions run history, or authorize a workflow dispatch.

`READY_FOR_AUTHORIZED_RERUN` means only that the static checks implemented here found no blockers in the supplied local snapshot. User authorization and actual scientific run evidence remain separate gates. Do not interpret source-pipeline artifact counts as verified equations.

The script is not run automatically by this change. No tests, validators, scientific experiments, paid/live API calls, or GitHub Actions workflows are executed during its creation.
## Verified stage correspondence

The three requested Core-295 IDs now have a verified Core-15 stage mapping, documented in [CORE295_STAGE_MAPPING_AUDIT.md](CORE295_STAGE_MAPPING_AUDIT.md): `exp295_ablation` follows `exp1_ablation`; `exp295` follows `exp1_ablation_aggregate`; and `exp295b` follows `exp1_five`. This resolves the naming/contract ambiguity only. The three Core-295 stages are still absent from `run_all.sh` and the dispatch workflow, so the readiness gate must continue to fail until their implementations and registration exist.

The structural-equivalence policy remains a draft with open design decisions. It must be explicitly frozen through a reviewed design decision; the readiness report must not infer approval from the existence of the draft.
## Task planning foundation

Once the catalogue meets the accepted/frozen contract, create a deterministic task manifest with [core295_plan_tasks.py](../scripts/core295_plan_tasks.py). The planner requires exactly 295 accepted entries (59 per domain), unique IDs/fingerprints and independence units, E4 review evidence, registered source records, complete variable ranges and ready generator contracts. It writes a new manifest with catalogue/task/shard hashes and exact-once domain-balanced shard assignments. It does not run experiments or accept equations. See [CORE295_TASK_PLANNER.md](CORE295_TASK_PLANNER.md).


## Same-run shard artifact contract

The Core-295 shard result envelope and strict exact-coverage verifier are documented in [CORE295_SHARD_RESULT_CONTRACT.md](CORE295_SHARD_RESULT_CONTRACT.md), with implementation in [core295_verify_shard_results.py](../scripts/core295_verify_shard_results.py). This is a verification-only prerequisite; no Core-295 runner, native payload aggregator, or workflow dispatch has been implemented.


## Core-295 shard execution driver

The fail-closed shard harness is documented in [CORE295_EXECUTION_DRIVER.md](CORE295_EXECUTION_DRIVER.md) and implemented in [core295_run_shard.py](../scripts/core295_run_shard.py). It requires a frozen 295-entry catalogue, exact manifest identity, and reviewed per-domain adapter callables. It is not wired into the runner or workflow; the current draft catalogue and missing domain adapters block execution.


The first five domain-guarded adapters are implemented for the restricted explicit-scalar generator contract. They share Core-15's unchanged data and ablation functions, but do not cover implicit, coupled, ODE, stochastic, or protocol-simulation equations. See [CORE295_EXECUTION_DRIVER.md](CORE295_EXECUTION_DRIVER.md). The catalogue must explicitly adopt and justify the adapter's independent-input sampling semantics per equation; merely changing generator status is not sufficient.
