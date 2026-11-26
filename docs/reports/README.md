# Benchmark performance reports

## Exp1 ablation — Core-15

- **Source report:** [exp1_ablation_performance_report.tex](exp1_ablation_performance_report.tex)
- **Evidence:** [GitHub Actions run #45869191966](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45869191966)
- **Evaluated commit:** `b460be2475ad9527bb7a56c9aaa11e740d26dea6`
- **Date:** 2026-11-26

The report evaluates PySR-only, HypatiaX with LLM, and HypatiaX without LLM on 15 equations. It distinguishes successful workflow execution from scientific performance and documents the limitations of the single-seed run, unequal compute budgets, missing/non-finite far-extrapolation cases, and the lack of statistically significant evidence for an LLM benefit.

The companion PDF was generated from this LaTeX source for convenient reading. The five recommended next steps are specified in the report: multi-seed replication, matched compute budgets, failure-aware aggregation, controlled LLM ablation, and complexity/scientific-validity checks.

To regenerate the PDF from the repository source, use a LaTeX installation with latexmk:

    latexmk -pdf -interaction=nonstopmode exp1_ablation_performance_report.tex

No benchmark was launched as part of preparing this report.
