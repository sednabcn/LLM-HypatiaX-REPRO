# HDS v50_2: research evolution, contribution, expectations, and reproducibility

**Status:** Research decision and experimental-design document; not a report of newly executed experiments.  
**Date:** 2026-11-27  
**Primary system:** HybridDiscoverySystem (HDS) v50_2

## Research question

Which gates and routing mechanisms improve analytical-expression discovery, under which conditions, and at what computational cost?

The recommended contribution is HDS v50_2's gating and routing architecture—not a blanket claim that every hybrid configuration beats a pure LLM.

## Main decisions

1. **Make HDS v50_2 the core system.** Focus on the gates and routing that decide when to accept an LLM-generated formula, combine it with a neural predictor, or use an alternative such as PySR.
2. **Use two recovery thresholds.** Primary practical threshold: `R² >= 0.99`. Strict near-exact predictive threshold: `R² >= 0.999999`. The strict threshold is not proof of symbolic equivalence. Since 0.99 may saturate across systems, it cannot support a superiority claim on its own.
3. **Resolve the hardcoded-formula bypass.** The supplied decision paper reports that EHSDeFi delegates to `PureLLMBaseline.generate_formula`, which tries hardcoded formulas before an LLM call. It reports identical formulas on 11 bypassed rows and missing formula provenance in M4. Disable the bypass for controlled comparisons and persist whether the LLM was called and which component produced each formula.
4. **Audit the evaluator.** Supplement A's Fix 5 evaluator is reported to retain an absolute `ss_tot > 1e-10` guard. Validate constant and near-constant targets, target scales, exact/perturbed predictions, non-finite values, and undefined R².
5. **Qualify M3/M4.** Keep claims exploratory until bypass attribution and evaluator behavior are validated. If M4 cannot be rerun in time, drop its headline claims rather than extending the schedule just to preserve them.
6. **Run a paired leave-one-gate-out ablation.** Use the same equations, samples, splits, seeds, and evaluation points across arms, with the bypass disabled.

## Ablation matrix

| Arm | Contribution isolated |
|---|---|
| Pure LLM baseline | Performance without hybrid routing |
| Full HDS v50_2 | Performance and cost of the complete system |
| Remove LLM acceptance gate | Whether acceptance prevents unsafe or incorrect formulas from controlling predictions |
| Remove probe gate | Whether probing improves route selection |
| Remove complexity routing | Whether complexity-aware selection matters |
| Remove NN augmentation | Whether NN predictions add value |
| Remove blend weight | Whether adaptive blending adds value over fixed/unweighted blending |
| Remove PySR prior | Whether the PySR search prior contributes |

Compare each arm using paired per-equation differences against both full HDS v50_2 and Pure LLM. Report uncertainty and avoid silently changing denominators between arms.

## Outcomes to report

- Practical and strict predictive recovery rates.
- Symbolic equivalence and numerical equivalence, independently assessed.
- Catastrophic failures, invalid expressions, numerical blow-ups, and worse-than-baseline cases.
- Availability and abstention rates, with reason codes.
- Generalisation/extrapolation under a declared protocol.
- Runtime, model/API calls, token or compute use, and PySR search cost.
- Per-case formula provenance, gate decisions, route, final predictor source, and all denominators.

## Expected interpretations (hypotheses, not findings)

| Possible result | Interpretation |
|---|---|
| Full HDS improves recovery and reduces catastrophic failures | Supports the complete architecture; ablations must identify which gates account for the gain |
| Only some gates help | Contribution is selective; retain useful gates and simplify or redesign neutral/harmful ones |
| Prediction improves but symbolic equivalence does not | Hybrid may be a useful predictor without demonstrating symbolic discovery |
| Failures decrease but average score falls | Reliability/accuracy trade-off that must be quantified |
| Pure LLM matches or exceeds HDS | Routing may be unnecessary under those conditions; report the null result |
| Effects vary by equation family or data condition | Build a condition-dependent route policy |
| M4 bypass cannot be resolved | Historical attribution remains ambiguous; keep exploratory or remove headline claims |

## Condition-dependent route map

Identify when the LLM formula, NN, PySR, blend, or abstention route should be preferred. Candidate factors include equation family/complexity, training sample count, noise, feature correlation, extrapolation distance, parseability, trust-gate result, probe result, and compute budget.

Classify conditions where Hybrid is better, comparable, worse, or unavailable relative to relevant baselines. Availability is not poor predictive quality: deliberate abstention or a missing candidate is not a low-scoring prediction. Report route-level outcomes by condition with uncertainty.

## Reproducibility requirements

For every case and arm, preserve stable case IDs and equation/domain metadata; data-generation settings and independent seed streams; exact train/validation/test and probe partitions; LLM provider/model/version, prompt provenance, decoding settings, call status and retries; hardcoded-bypass status and formula source; evaluator version and symbolic assumptions; every gate result and rejection reason; probe diagnostics, complexity score, PySR configuration, blend weights and final route; final predictor source, metrics, runtime and failure reason.

Test labels must not inform prompts, gate calibration, route selection, or hyperparameter tuning. Disclose whether query-batch covariates influence routing (transductive evaluation) or prediction uses training-only calibration (inductive evaluation).

## Recommended execution sequence

1. Audit and disable the hardcoded-formula bypass in the controlled comparison path; verify actual LLM calls and formula provenance.
2. Validate the evaluator, especially its total-sum-of-squares guard for degenerate and near-constant targets.
3. Freeze case list, data generation, splits, seeds, thresholds, LLM settings, PySR budget, and output schema.
4. Run Pure LLM and full HDS v50_2 on paired conditions.
5. Run leave-one-gate-out arms, changing one mechanism at a time.
6. Analyse by equation family, data condition, route, availability, extrapolation, and cost.
7. Reassess M3/M4; revise the abstract only after validated outputs exist.

## Evidence boundary

This document is based on the supplied decision paper. It does not independently inspect the EHSDeFi implementation, Supplement A Listing 8, M3/M4 raw artifacts, or the pasted noise-sweep output. The bypass and evaluator concerns are reported findings requiring source-level confirmation. It does not claim the bypass has been disabled, the evaluator fixed, or the ablation completed.

No new benchmark, model training, LLM request, or GitHub Actions experiment workflow was launched to prepare this document. Expected outcomes are hypotheses; no proposed experiment is represented as completed.

## Build the PDF

The PDF is generated from the companion LaTeX source using `pdflatex` (run twice to resolve the table of contents):

```bash
pdflatex -interaction=nonstopmode -halt-on-error HDS_v50_2_RESEARCH_EVOLUTION_AND_REPRODUCIBILITY.tex
pdflatex -interaction=nonstopmode -halt-on-error HDS_v50_2_RESEARCH_EVOLUTION_AND_REPRODUCIBILITY.tex
```
