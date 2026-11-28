# Retrospective DeFi Random 40/60 vs PCA 40/60 audit

**Audit date:** 2026-11-28  
**Repository:** `sednabcn/LLM-HypatiaX-REPRO`  
**Method:** reusable `hypatiax.experiments.audit.audit_formula` API (restricted AST/SymPy evaluator)  
**Execution:** GitHub Actions run [46135085979](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46135085979)  
**Scope:** read-only analysis of committed JSON artifacts. No model training, experiment reruns, or LLM calls.

## 1. Coverage and answer-key provenance

The audit read five seed files per protocol (42, 99, 123, 777, 2024), with 74 equation cases per seed.

| Protocol | Records | Saved formulas | Ground-truth expressions | Answer-key source |
|---|---:|---:|---:|---|
| Random 40/60 | 370 | 370 | 370 | `protocol_metadata` |
| PCA 40/60 | 370 | 370 | 370 | `protocol_metadata` |
| **Total** | **740** | **740** | **740** | |

All 740 records mark `ground_truth_excluded_from_prompt=true`. This corrects the November 27 report's assertion that historical answer keys were absent: the current canonical raw artifacts do contain persisted answer-key expressions. The earlier all-missing assertion in the integrity test was stale and has been corrected in the accompanying PR.

## 2. Symbolic-equivalence results

| Protocol | Exact symbolic equivalent | Not assessable | Not symbolically equivalent |
|---|---:|---:|---:|
| Random 40/60 | 85 (22.97%) | 265 (71.62%) | 20 (5.41%) |
| PCA 40/60 | 85 (22.97%) | 265 (71.62%) | 20 (5.41%) |
| **Combined** | **170 (22.97%)** | **530 (71.62%)** | **40 (5.41%)** |

The identical counts are expected here: both protocols contain the same 74 equation cases repeated across the same five seeds. The counts are case-seed observations, not 740 independent equation families.

### Not assessable: primary causes

The reusable evaluator correctly refuses to infer variable aliases. The dominant reason is that persisted ground-truth expressions use names that are not mapped to the saved `variable_names` schema.

| Cause | Random | PCA |
|---|---:|---:|
| Unmapped ground-truth symbols | 223 | 224 |
| Assignment shadows a parameter/private name | 22 | 21 |
| Unsupported `dot` / `where` calls | 10 | 10 |
| Formula structure / syntax errors | 9 | 9 |
| Unsupported conditional expression | 1 | 1 |
| **Total not assessable** | **265** | **265** |

These are evaluator/provenance limitations, not symbolic failures. Resolving them requires authoritative alias mappings or a deliberate extension of the safe evaluator, not guessed substitutions.

### Not symbolically equivalent

The 20 non-equivalent cases per protocol are four liquidation-price equations repeated across five seeds:

- Liquidation Price Long
- Liquidation Price Short
- Liquidation price for leveraged long
- Liquidation price for leveraged short

The saved formula and stored ground truth differ in the liquidation coefficient (including a 0.2 coefficient in the generated leveraged-long/short formulas versus 1.25 in the stored answer key, and missing 1.25 factors in the other two formulas). Under the persisted expressions and current variable mapping, the safe evaluator finds these pairs formally non-equivalent. This result is repeated in both protocols and all five seeds.

## 3. Selected-predictor performance and routing

Selected-predictor test R² is reported separately from symbolic status.

| Statistic | Random 40/60 | PCA 40/60 |
|---|---:|---:|
| Finite selected-predictor scores | 370 | 365 |
| Median selected-predictor test R² | **0.99723** | **0.96611** |
| Mean selected-predictor test R² | **0.81624** | **-5.74082** |

The PCA mean is strongly affected by extreme negative R² outliers; its median is the more robust central summary. One PCA score per seed is undefined and excluded (365 finite scores). All 370 Random scores are finite.

| Route decision | Random 40/60 | PCA 40/60 |
|---|---:|---:|
| NN abstention / fallback | 248 | 254 |
| NN | 62 | 57 |
| Ensemble | 60 | 59 |
| **Total** | **370** | **370** |

The saved formula being checked is the LLM/hybrid formula. The selected-predictor score describes the routed predictor actually selected for the case. Neither predictive R² nor route selection is a substitute for symbolic equivalence.

## 4. Conclusions and next steps

1. The current committed artifacts contain answer keys for every one of the 740 records, with explicit protocol-metadata provenance and prompt exclusion.
2. Only 170/740 case-seed records are formally equivalent under the existing safe evaluator.
3. 530/740 are not assessable, predominantly because the ground-truth symbol names lack explicit alias mappings. Do not count these as successes or failures.
4. 40/740 are formally non-equivalent under the stored answer keys; these are four liquidation-price cases repeated across the five seeds in each protocol.
5. Random 40/60 has a higher median selected-predictor test R² than PCA 40/60. The PCA mean is dominated by extreme negative outliers.
6. The system is a routed hybrid predictor: report LLM formula equivalence, selected-predictor performance, and route choice as separate outcomes.

The raw result files were not modified. The generated machine-readable case-level report is available as the `defi-4060-retrospective-audit` artifact attached to [run 46135085979](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46135085979).
