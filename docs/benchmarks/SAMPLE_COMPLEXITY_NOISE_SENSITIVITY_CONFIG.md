# Sample-Complexity and Noise-Sensitivity Benchmark Configuration

This note records the intended configuration and interpretation rules for the Feynman
sample-complexity and noise-sensitivity benchmarks. It separates the recommended
configuration for an official full-pipeline rerun from what can be established about
the historical result files. It does not itself certify or validate any experiment.

## 1. Sample-complexity benchmark

### Sample-size grid

Use the following training-sample counts:

| Training samples (N) | Historical result shard |
|---:|---|
| 50 | `sample_complexity_20260812_180017_nshards01` |
| 100 | `sample_complexity_20260812_180007_nshards02` |
| 200 | `sample_complexity_20260812_180009_nshards03` |
| 500 | `sample_complexity_20260812_180010_nshards04` |
| 750 | `sample_complexity_20260812_180024_nshards05` |
| 1000 | `sample_complexity_20260812_180011_nshards06` |

The historical design contains 30 equations at each sample count. Each listed result
file represents one sample-count shard; data-efficiency curves must therefore be
computed after combining all six sample-count outputs, not independently within a
single shard.

The benchmark script's built-in default grid is `{50, 100, 200, 500}`. The full
six-point historical grid is supplied through the task/sample-count configuration
(e.g. `SC_SAMPLE_COUNTS`). The runner's `FEYNMAN_SAMPLES` default of 200 is not,
by itself, evidence that every shard ran at N=200: the assigned `sc_n{N}` task
overrides the per-worker effective sample count. Record the effective N for every
shard.

### Primary success threshold

For comparable sample-complexity curves, use one fixed threshold across all N:

- **Primary:** R² ≥ 0.99.
- **Sensitivity analysis:** also report R² ≥ 0.999, clearly labelled as a stricter
  secondary threshold.

Do not use a threshold ladder that changes with N for the primary curve. Historical
CSV outputs show varying thresholds (approximately 0.999 to 0.9999, depending on N);
the result files do not have sufficient provenance to establish the exact command or
configuration that produced every historical threshold. The current script's
non-legacy default is a fixed 0.99 threshold; its legacy-threshold option should not
be used for the primary cross-N comparison.

### Eligibility and reporting

- Exclude rows explicitly marked `exclude_from_reported_results=True`, including
  unverified/no-formula rows such as the historical all-domains
  `HybridSystemLLMNN` entries.
- Report eligible equation counts and denominators for every method and N.
- Compute `min_n_above_threshold` only after joining the outputs for all six N values.
- Plot or tabulate the fraction of eligible equations above the same R² threshold
  against N. Do not interpret a single shard's within-shard minimum-N statistic as a
  cross-sample-size data-efficiency result.

## 2. Noise-sensitivity benchmark

The current noise-sweep benchmark configuration covers:

`0%, 0.05%, 0.1%, 0.5%, 1%, 5%, 10%` noise.

The historical result set inspected for this audit contains only the first five levels
(0% through 1%). The 5% and 10% levels are part of the current full grid but are not
represented in those historical files. Do not describe the historical five-file set
as a completed seven-level sweep.

Use a common R² ≥ 0.99 reporting threshold across noise levels, with R² ≥ 0.999 as an
optional stricter sensitivity analysis. Apply the same eligibility/exclusion rules at
every noise level and report the eligible denominator. A high pass count in historical
files is descriptive only: those files are marked as lacking verified provenance and
cannot alone establish validated robustness.

## 3. Provenance required for an official run

For every sample-count shard and noise-level shard, persist a machine-readable
manifest containing at least:

- experiment name and protocol/version;
- source commit SHA and benchmark script path/version;
- run ID, shard/task ID, and completion status;
- random seed and any seed derivation rule;
- effective training sample count (for sample complexity);
- effective noise level and noise-generation convention (for noise sensitivity);
- R² threshold(s), metric definition, and row eligibility/exclusion policy;
- method/model configuration and relevant dependency/runtime versions;
- equation IDs and input/split fingerprints, where applicable;
- output artifact names and checksums.

The aggregate must verify that all expected shards are present, that their protocol and
configuration agree, and that each expected equation/method/condition is represented
before publishing aggregate curves or summary claims. Missing provenance must be
reported as a limitation; it must not be silently inferred from filenames.

## 4. Interpretation of the inspected historical results

The historical sample-complexity files cover N = 50, 100, 200, 500, 750, and 1000,
with 30 equations per file. Recomputed at a common R² threshold of 0.999, the
Enhanced Hybrid counts were 29/30, 30/30, 30/30, 30/30, 30/30, and 30/30,
respectively. This is already near-ceiling performance at the smallest N and does not
show a clean, steadily increasing trend. At R² ≥ 0.99, Enhanced Hybrid was 30/30 at
every N. Treat these as descriptive historical calculations, not official validated
results: all six files are marked `NO_PROVENANCE` in the audit manifest.

For the five historical noise levels (0%, 0.05%, 0.1%, 0.5%, 1%), Enhanced Hybrid
was 30/30 at R² ≥ 0.99 in the inspected files. These files are also marked
`NO_PROVENANCE`; this is not sufficient evidence for a robustness claim.

## 5. Relevant implementation and result locations

- Runner: `hypatiax/experiments/benchmarks/run_sample_complexity_benchmark.py`
- Historical sample-complexity outputs:
  `hypatiax/data/results/comparison_results/feynman-tests/sample-complexity/`
- Historical noise-sweep outputs:
  `hypatiax/data/results/comparison_results/feynman-tests/noise-sweep/`
- Audit provenance manifest: `archive/audit/audit_out/results_manifest.csv`

## 6. Official validation policy

The official validation is the full pipeline rerun with the documented configuration
and complete provenance. Historical outputs and partial checks are useful for audit
and comparison, but do not substitute for that full rerun. No experiment is launched
by this documentation change.
