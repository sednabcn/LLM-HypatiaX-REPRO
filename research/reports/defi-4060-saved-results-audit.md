# Offline symbolic audit of saved DeFi 40/60 results

## Scope

This post-hoc audit targets the five committed seeds for each of:

- `exp1_4060_seeds`: Random 40/60 split.
- `exp1b_pca`: PCA 40/60 split.

It reads JSON result files already committed under `hypatiax/data/results`. It does not call benchmark entry points, train models, call an LLM, regenerate predictions, or modify the source result files.

## Input coverage inspected on master

The saved files contain 74 records per seed. Metadata inspection of the exact per-seed inputs found:

| Experiment | Records | Saved hybrid formulas | Ground-truth expressions | Variable schemas | Constants maps |
|---|---:|---:|---:|---:|---:|
| Random 40/60 | 370 | 370 | 370 | 370 | 370 |
| PCA 40/60 | 370 | 370 | 370 | 370 | 370 |
| **Total** | **740** | **740** | **740** | **740** | **740** |

The Random seed-42 input is the un-suffixed `hypatiax_defi_benchmark_v3c_4060_results.json` named in the experiment summary. PCA uses the five explicitly seed-named files. The older un-suffixed PCA result file is deliberately excluded because it is not one of the five files listed by the five-seed summary.

## Run the symbolic audit locally

From the repository root:

```bash
python scripts/analysis/audit_saved_defi_4060.py
```

The default output is `research/reports/defi-4060-symbolic-audit.json`. The report records a per-case symbolic status and aggregates exact-equivalence, non-equivalence, and not-assessable outcomes separately.

## Interpretation

The audit compares the saved `results.hybrid.formula` against the saved protocol answer key using the restricted AST/SymPy evaluator exposed through `hypatiax.experiments.audit`. It does not use test R² as a proxy for symbolic correctness. Missing or unmapped metadata stays not assessable; no answer keys or aliases are inferred.

The committed result files are inputs only. The generated report is a separate output and must not be used to overwrite historical benchmark metrics.
