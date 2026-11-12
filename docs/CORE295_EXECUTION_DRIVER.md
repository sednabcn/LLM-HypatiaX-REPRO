# Core-295 shard execution driver

**Status:** fail-closed adapter harness. Domain-specific scientific adapters are not yet implemented.  
**Branch:** `promotion/rerun-code-review`

## Driver boundary

`scripts/core295_run_shard.py` owns the orchestration boundary for one planned shard:

1. Requires the exact catalogue bytes hashed into the task manifest.
2. Requires a frozen, ready 295-entry catalogue: 59 accepted equations per domain, complete model-class and variable-role declarations, generator contracts, and train/extrapolation ranges for independent inputs only.
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


## Initial domain adapter implementation

Five domain-guarded entry points now share a deliberately narrow scalar-expression implementation:

- `hypatiax.experiments.benchmarks.core295_adapters.chemistry:run_equation`
- `hypatiax.experiments.benchmarks.core295_adapters.biology:run_equation`
- `hypatiax.experiments.benchmarks.core295_adapters.physics:run_equation`
- `hypatiax.experiments.benchmarks.core295_adapters.defi_amm:run_equation`
- `hypatiax.experiments.benchmarks.core295_adapters.defi_risk:run_equation`

All five delegate to `core295_adapters.common`. The shared adapter converts one accepted catalogue record using the existing restricted symbolic parser in `core295_catalogue.py`, then calls the existing Core-15 `generate_data`, `generate_extrap_data`, and `run_condition` functions. It does not modify the Core-15 implementation or reuse Core-15 equation indices. Core-15's 200-point, 5%-noise training generator, 80/20 split, 100-point near/medium/far extrapolation and native per-arm method defaults remain in force.

This adapter supports only the explicit scalar contract below. It intentionally refuses other generator models rather than silently flattening them:

```json
{
  "status": "ready",
  "method": "catalogue_expression_v1",
  "seed_policy": "sha256_run_equation_v1",
  "parameter_sampling": "independent_uniform_over_declared_ranges",
  "sampling_semantics": "all_declared_variables_are_independent_inputs"
}
```

Every declared variable is sampled as an independent feature from its own train/extrapolation intervals. This is a substantive modeling assumption: if a symbol is a fixed physical parameter, a dependent state, a coupled-system variable, or a constrained protocol variable, this generic contract is inappropriate until an equation-specific generator is specified. Do not set this contract merely to make an entry pass readiness. The equation must also parse as one scalar explicit expression in the restricted grammar. Implicit systems, ODEs, piecewise/protocol simulators, stochastic processes, and equations requiring fixed constants or coupled constraints need separately reviewed generator implementations.

The adapter hashes the full generated training arrays, the actual train/test split, and each extrapolation set into every arm payload. It derives the task seed from the driver's SHA-256 seed material. It refuses a name collision with Core-15's EQ_ID table. The live `hypatia` arm is marked skipped unless `--allow-live-services` is supplied; when authorized but the API key is absent, it is explicitly failed. The two non-live arms still run when the adapter is invoked. A skipped or failed arm is not scientific success.

Example domain adapter arguments for a shard containing all five domains:

```bash
--adapter 'Chemistry=hypatiax.experiments.benchmarks.core295_adapters.chemistry:run_equation' \
--adapter 'Biology=hypatiax.experiments.benchmarks.core295_adapters.biology:run_equation' \
--adapter 'Physics=hypatiax.experiments.benchmarks.core295_adapters.physics:run_equation' \
--adapter 'DeFi AMM=hypatiax.experiments.benchmarks.core295_adapters.defi_amm:run_equation' \
--adapter 'DeFi Risk=hypatiax.experiments.benchmarks.core295_adapters.defi_risk:run_equation'
```

The task planner now also requires `generator.sampling_semantics`. This prevents a catalogue from appearing executable with only a method label and an underspecified sampling assumption.

**Scope limit:** these are five domain-checked adapters for one shared scalar benchmark contract, not five scientifically bespoke simulators. More specialized equation classes require explicit implementations and review before acceptance. No adapter, model, generator, test, validator, API, experiment, or workflow was executed while adding these files.


## Model-class and variable-role gate

The task planner and shard driver now require each accepted entry to declare a supported `model_definition.model_class` and matching `generator.model_class`. The variable dictionary must be partitioned exactly into independent inputs, dependent variables, dynamic states, fixed parameters, and physical constants. Input ranges must cover only independent inputs; fixed parameters and constants are not silently sampled as features. The generator must also declare parameter-sampling scope and an explicit boolean stating whether its constraints are enforced.

The supported class labels are `explicit_scalar`, `implicit_scalar`, `coupled_algebraic_system`, `ode_ivp`, `difference_system`, `stochastic_process`, `protocol_simulation`, and `matrix_operator`. These labels are a classification gate, not a promise that an adapter exists. The shared `core295_adapters.common` implementation remains limited to its exact all-variables-independent scalar contract. Other classes require their own reviewed adapter implementation and scientifically appropriate data-generation contract.

See [Core-295 generator taxonomy and current catalogue triage](CORE295_GENERATOR_TAXONOMY_AND_CATALOGUE_TRIAGE.md). The current 24-entry catalogue has not yet been annotated with these roles, so it remains blocked from planning and execution. This change is a fail-closed schema/driver improvement, not a claim of new scientific coverage.


The common scalar adapter was further restricted: it now refuses any entry whose declared variables include fixed parameters, physical constants, dependent variables, or dynamic states. It requires every declared symbol to be an independent input with a corresponding range. This is intentionally stricter than the general planner contract. A model can be classified as `explicit_scalar` and still require a dedicated parameter-aware generator; the label alone does not make it compatible with the shared adapter. The catalogue's current model-class annotations are preliminary, and all generator statuses remain pending.
