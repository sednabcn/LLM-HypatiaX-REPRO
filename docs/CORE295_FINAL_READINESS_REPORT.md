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
