# 40/60 and PCA benchmark report: seed-level results, small-data effects, and symbolic-recovery audit

**Repository:** `sednabcn/LLM-HypatiaX-REPRO`  
**Prepared:** 2026-11-27  
**Scope:** Existing five-seed PCA 40/60 and random 40/60 DeFi benchmark outputs; source-level audit and proposed follow-up experiments.  
**Execution status:** This report documents existing runs and source inspection only. No benchmark, training job, synthetic-data sweep, or workflow was launched while preparing it.

## 1. Executive summary

The existing experiments do not establish that the LLM is insensitive to training-set size, nor that the neural network alone explains the change in hybrid behaviour. They do establish several reasons to investigate the data path before interpreting a “zero recovery” result:

1. Both PCA and random 40/60 runs hold out 60% of the generated rows. They are not 80/20 experiments.
2. The NN path further withholds 20% of its outer training partition for validation. Ignoring the minimum-five-row guard, the approximate all-data proportions are therefore 32% NN fit / 8% NN validation / 60% test for 40/60, compared with 64% / 16% / 20% for an 80/20 outer split.
3. The hybrid is not an LLM-only arm. It receives the NN result, and its routing, trust gates, diagnostics, candidate selection, and final evaluation can depend on NN predictions or metrics. The LLM model being the same is therefore not sufficient to hold the hybrid pipeline constant.
4. The current 4060 validator labels an (R^2 \ge 0.999999) threshold as a “solve”. This is not symbolic equivalence. A high predictive (R^2) is not proof that the recovered expression is algebraically identical to the target.
5. The compact PCA pooled report exposes per-seed raw means, and the experiment summary exposes solve-threshold counts, but neither provides a complete seed-level table of mean, median, and a separately defined FAR-OO metric. The medians below are taken from the inspected per-seed result analysis; FAR-OO is explicitly marked unavailable rather than inferred.

**Main conclusion:** the “0 recovery” interpretation must be suspended until symbolic equivalence is measured independently. In parallel, the NN/data-volume hypothesis is testable with controlled synthetic equations and repeated sampling.

## 2. PCA 40/60 results by seed

Source run: `exp1b_pca`, five seeds `42, 99, 123, 777, 2024`; 74 equations per seed; 370 validated raw case records. The PCA protocol is documented as a directed outer split using PCA PC1, with 40% train and 60% test.

### 2.1 Seed-level test (R^2)

The table combines the per-seed raw mean (R^2) values in `hypatiax_defi_benchmark_pca_pooled_seed_report.json` with per-seed median values from the five-seed result analysis. These are hybrid and NN predictive test-(R^2) summaries, not symbolic-equivalence scores.

| Seed | NN mean (R^2) (raw) | NN median (R^2) | Hybrid mean (R^2) (raw) | Hybrid median (R^2) | FAR-OO |
|---:|---:|---:|---:|---:|---|
| 42 | -17.5855 | 0.8479 | 0.08408 | 0.9807 | Not separately recorded |
| 99 | -46.5346 | 0.8889 | 0.08364 | 0.9590 | Not separately recorded |
| 123 | -46.7053 | 0.8756 | 0.10129 | 0.9607 | Not separately recorded |
| 777 | -38.6066 | 0.8854 | 0.05711 | 0.9664 | Not separately recorded |
| 2024 | -7.7750 | 0.9150 | 0.09005 | 0.9761 | Not separately recorded |

**Important interpretation:** the gap between mean and median is very large, especially for NN and hybrid. The raw means are dominated by a small number of extremely poor/negative (R^2) cases. The median describes the typical case more robustly, but it must not replace the mean: both are needed to expose the tail. The hybrid mean-of-seed-means is approximately 0.08324; its mean of seed medians is approximately 0.96858. For NN, the corresponding values are approximately -31.4414 and 0.88257.

The pooled report also records clipped-to-([-10,1]) means: NN mean-of-seed-means clipped = -1.27811; hybrid = 0.46944. Clipping is a secondary robustness summary and must always be labelled; it is not the raw (R^2).

### 2.2 PCA threshold counts

The committed `exp1b_pca_summary.json` reports:

| Seed | Threshold passes | Finite hybrid (R^2) denominator | Rate |
|---:|---:|---:|---:|
| 42 | 8 | 73 | 10.96% |
| 99 | 7 | 73 | 9.59% |
| 123 | 5 | 73 | 6.85% |
| 777 | 7 | 73 | 9.59% |
| 2024 | 8 | 73 | 10.96% |
| **Total** | **35** | **365** | **9.59%** |

The five omitted records are the Kelly case, whose hybrid target is constant and for which test (R^2) is undefined. The raw coverage remains 370/370 records. These 35 passes mean only that the hybrid test (R^2) crossed the validator threshold (0.999999). They must not be called exact symbolic recoveries.

### 2.3 FAR-OO metric availability

No field called FAR-OO (or a clearly equivalent, explicitly defined far-out-of-range score) is present in the compact pooled report or summary used for this table. The full records contain train/test arrays, predictions, split metadata, and OOD diagnostics, but a named FAR-OO aggregate must be computed from a declared protocol before reporting it. In particular, do not silently equate FAR-OO with ordinary random/PCA held-out test (R^2), extrapolation gap, or an OOD diagnostic flag.

To complete this table, define FAR-OO operationally (far-range boundary, direction, distance from training support, scoring metric, and aggregation), then rescore the saved predictions or rerun only if the required far-range test data were not saved.

## 3. Random 40/60 benchmark results by seed

Source run: GitHub Actions run [#354](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46021448210), five isolated workers, 74 equations per seed, 370 raw records. One intractable IL-breakeven case per seed has no valid scored (R^2), leaving 73 scored cases per seed and 365 overall.

| Seed | NN median (R^2) | Hybrid median (R^2) | NN mean (R^2) | Hybrid mean (R^2) | NN (R^2>0.9) | Hybrid (R^2>0.9) | Hybrid (R^2>0.99) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 0.997434 | 0.997784 | 0.838399 | 0.851478 | 55/73 | 61/73 | 49/73 |
| 99 | 0.997088 | 0.997375 | 0.800380 | 0.826653 | 57/73 | 60/73 | 50/73 |
| 123 | 0.994727 | 0.996917 | 0.787284 | 0.805541 | 55/73 | 58/73 | 50/73 |
| 777 | 0.994632 | 0.995812 | 0.849594 | 0.866334 | 57/73 | 63/73 | 51/73 |
| 2024 | 0.996528 | 0.997147 | 0.745069 | 0.760634 | 52/73 | 56/73 | 47/73 |

Across 365 scored records, NN (R^2>0.9): 276/365 (75.62%); hybrid (R^2>0.9): 298/365 (81.64%); hybrid (R^2>0.99): 247/365 (67.67%). Mean of per-seed medians: NN 0.9961, hybrid 0.9970. Mean of per-seed means: NN 0.8041, hybrid 0.8221. Mean per-seed median runtime: NN 0.340 s, hybrid 1.448 s (about 4.26x).

These are predictive metrics for the random 40/60 run. The validator's (0.999999) “solve” label is again an (R^2) threshold, not a symbolic proof.

## 4. What the split code implies

### 4.1 Outer split

The random benchmark's `_random_split_random_40_60` creates one seeded random permutation and holds out the first `ceil(0.6*n)` rows. The PCA benchmark uses a PCA-directed 40/60 split. These are different outer split strategies, but both nominally allocate 40% to outer training and 60% to held-out testing.

### 4.2 NN validation split

The NN training path then takes approximately 20% of `X_train` as an internal validation subset (with a minimum of five rows). The current metadata selects the high edge of feature index 0 for validation. The NN fits on the remaining outer-training rows. Thus, for sufficiently large datasets:

- 40/60 outer split: about 32% fit, 8% validation, 60% test.
- 80/20 outer split: about 64% fit, 16% validation, 20% test.

This is a real change in effective NN fitting sample count, not evidence of a hidden change to the outer 40/60 split. Exact counts depend on each equation's generated row count and the minimum-validation rule.

### 4.3 Hybrid dependence on NN

The benchmark calls the hybrid with the same outer arrays plus `nn_result=nn_m` and split metadata. The recorded hybrid output includes NN selection, abstention, edge (R^2), Ridge eligibility, trust-gate diagnostics, NN prediction validation, degradation probes, OOD diagnostics, and blend weights. Consequently, an unchanged LLM model/prompt does not guarantee an unchanged hybrid decision. The NN can affect routing, acceptance, candidate checks, or blending.

A clean attribution requires three separately reported outcomes:
- **LLM-only:** generated formula evaluated without NN candidate selection or NN-derived gate signals.
- **NN-only:** predictive (R^2) and calibration on the same test arrays.
- **Hybrid:** the complete deployed pipeline, with every NN-dependent decision recorded.

## 5. Why “zero symbolic recovery” is not yet established

The 4060 validator's `finite_r2` reads `results.hybrid.test_r2`; its `finalize` function increments the “solve” count when this predictive score is at least (0.999999). This measures near-perfect predictive agreement on the held-out sample, not algebraic equivalence of the generated formula.

A valid symbolic-recovery evaluator should:
1. Parse the generated expression into a restricted symbolic AST (or a safely constrained symbolic representation).
2. Normalize expressions where mathematically justified.
3. Compare candidate and target by symbolic simplification of their difference, with domain/assumption checks.
4. Independently test numerical equivalence over fresh, non-training points, including singularities, sign/domain constraints, and boundary cases.
5. Distinguish exact equivalence, numerical equivalence within tolerance, partial recovery, invalid/unparseable formula, abstention, and no LLM call.
6. Preserve provenance: formula text, prompt/input sample, model identifier, temperature, token limits, retry count, and the exact target expression.

A formula can have (R^2=1) on a finite sample and still be algebraically wrong. Conversely, an algebraically equivalent formula can receive a poor (R^2) if evaluation mishandles domains, constants, units, or numerical stability.

## 6. Deeper investigation: low-data randomness and synthetic datasets

The low-data hypothesis is plausible and testable. It should be investigated as a controlled study rather than by changing several hyperparameters at once.

### 6.1 Core factorial experiment

Build a synthetic equation suite with known ground-truth expressions and deterministic sample generators. Cover:
- Linear and affine functions.
- Polynomial functions of increasing degree and interaction order.
- Rational functions with poles and restricted domains.
- Exponential/logarithmic functions.
- Trigonometric functions.
- Piecewise and threshold functions.
- Multivariate functions with correlated and redundant inputs.
- Functions with additive and multiplicative constants, scale disparities, and controlled noise.

For each equation family, vary independently:

| Factor | Suggested levels |
|---|---|
| Outer training fraction | 10%, 20%, 40%, 60%, 80% |
| Train sample count | e.g. 8, 16, 32, 64, 128, 256 |
| Sampling design | uniform random, Latin hypercube, clustered, boundary-biased, PCA-directed |
| Noise | 0, low, moderate; separately test heteroscedastic noise |
| Feature correlation | independent, moderate, near-collinear |
| NN capacity | small, current, larger |
| Regularisation | current, stronger L2, dropout, early-stop variants |
| NN seeds | multiple independent initialisations |
| Data seeds | multiple independent sample draws |
| LLM | fixed model, prompt, temperature, token budget and retries |

Use a fixed, large, independent evaluation grid per equation, and keep it identical across methods and sample sizes. Separate interpolation and far-out-of-range (FAR-OO) test regions. Do not let the LLM or model-selection logic see the final test labels.

### 6.2 Randomness decomposition

A single seed conflates several sources of variability. Record independent seed streams for:
- Synthetic data generation.
- Outer split selection.
- NN weight initialisation/training order.
- Any candidate generation or stochastic decoding (if enabled).
- Bootstrap/resampling used for confidence intervals.

Use a crossed design: for each data seed, repeat multiple NN seeds; for each training fraction, preserve nested subsets of a common master sample. This isolates the effect of sample count from the effect of drawing a different dataset. Report mean, median, standard deviation, interquartile range, and confidence intervals across repetitions—not only a best seed or pooled case count.

### 6.3 Regularisation study

At low sample counts, compare:
- Current NN configuration.
- Smaller NN / lower parameter count.
- L2 weight decay grid.
- Dropout grid, if compatible with the architecture.
- Early stopping with validation-size sensitivity.
- Ridge and other simple baselines.
- Training-mean baseline.
- A symbolic/regression baseline that does not depend on the LLM.

Tune on a validation partition nested entirely inside the training data. Never use the final test/FAR-OO data to select regularisation. Include learning curves and train-versus-validation gaps. Since the current validation rule selects an edge of feature 0, compare it with random validation, stratified validation, and a validation design that reflects the intended deployment distribution.

### 6.4 LLM/hybrid ablations

Hold the LLM fixed and run these arms:
1. LLM formula generation from the equation description only.
2. LLM generation with a fixed number of labelled training examples.
3. LLM generation with NN predictions supplied.
4. Full current hybrid including NN-dependent routing/gates.
5. Hybrid with NN gates disabled (diagnostic only).
6. Hybrid with a simple Ridge/linear surrogate replacing the NN signal.

Record whether the LLM was actually called, whether it returned a parseable formula, whether the formula passed trust gates, which gate rejected it, and whether the final score came from the formula, NN, Ridge, or blend. This separates “no symbolic candidate”, “candidate rejected”, and “candidate generated but evaluated badly”.

## 7. Other high-priority explanations for low or zero recovery

1. **Metric/label mismatch:** predictive (R^2) is currently being used as a symbolic-solve proxy in the 4060 validator.
2. **Target expression and domain:** equivalent expressions may differ syntactically; restricted domains, singularities, constants, units, and branch choices need explicit handling.
3. **Prompt information changes:** same LLM model does not imply same prompt. Check number and selection of examples, formatting, variable names, metadata, context truncation, and whether training samples are included.
4. **NN-dependent routing:** abstention, trust gates, degradation probes, Ridge eligibility, or blend weights may suppress or override a correct LLM formula.
5. **Small-sample identifiability:** many expressions can interpolate a small sample. More regularisation cannot resolve an underdetermined symbolic problem without structural priors or informative sampling.
6. **PCA split transductivity and orientation:** PCA is fitted on raw unstandardized features and the split is directed along PC1. This creates a distribution different from random holdout and may concentrate test points at one end of the dominant direction.
7. **Feature-0 validation bias:** the NN internal validation subset is selected by an edge of feature 0, which may not represent the full test distribution, especially for correlated features.
8. **Unequal effective fit counts:** small datasets are affected disproportionately by the minimum-five validation guard and rounding.
9. **LLM nondeterminism and retries:** log requested versus actual temperature, provider/model version, retry count, request failures, and token truncation. If temperature is nominally fixed but decoding or service versions vary, the run is not strictly deterministic.
10. **Numerical conditioning:** scaling, ill-conditioned features, target magnitude, overflow/underflow, and singular expressions can break numerical checks despite a correct formula.
11. **Case composition and denominators:** report raw records, finite-score denominators, intractable cases, constant targets, failed model calls, and undefined metrics separately. Never silently drop failed or undefined cases.
12. **Data leakage / hidden partitions:** audit every generator, split function, model-specific validation partition, and hybrid probe. Persist exact row indices or stable row IDs and prove that no test labels enter training, prompt construction, gates, or hyperparameter selection.

## 8. Recommended order of work

**Phase 1 — Measurement integrity (no benchmark run required):**
- Correct terminology in validators: rename (R^2)-threshold “solve” to “near-perfect predictive (R^2) pass”.
- Add a separate symbolic-equivalence evaluator and explicit recovery categories.
- Build a per-case audit table containing outer train/test counts, NN fit/validation counts, formula provenance, LLM call status, routing decision, gate outcomes, and all denominators.
- Complete PCA mean/median/FAR-OO reporting from raw records once FAR-OO is defined.

**Phase 2 — Source/data-flow audit:**
- Trace each synthetic generator and its support/range construction.
- Verify the exact data and prompt inputs consumed by LLM and hybrid.
- Verify that all gates use training-only signals.
- Verify split indices are disjoint and exhaustive, with no duplicate or leaked rows.

**Phase 3 — Synthetic controlled study:**
- Implement the factorial design in Section 6.
- Start with a small, deterministic subset of equation families and sample sizes.
- Validate the symbolic evaluator against known equivalent and deliberately non-equivalent formulas.
- Only then expand the sweep.

**Phase 4 — Regularisation and hybrid ablations:**
- Tune NN regularisation on nested validation data.
- Compare NN-only, LLM-only, and hybrid under identical samples and test points.
- Quantify uncertainty over both data seeds and NN seeds.

## 9. Sources and reproducibility pointers

- PCA seed summary: `hypatiax/data/results/comparison_results/noise-noiseless/15_pca/exp1b_pca_summary.json`
- PCA pooled seed means: `hypatiax/data/results/comparison_results/noise-noiseless/15_pca/hypatiax_defi_benchmark_pca_pooled_seed_report.json`
- PCA runner: `scripts/ci/run_exp1b_pca.sh`
- PCA validator: `scripts/ci/exp1b_pca_seed_outputs.py`
- PCA benchmark: `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py`
- Random 40/60 benchmark: `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c_4060.py`
- Random 40/60 validator: `scripts/ci/exp1_4060_seed_outputs.py`
- Random 40/60 run #354: https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46021448210

**Caveats:** This is a documentation and research-plan change. The numeric PCA seed medians are reproduced from the inspected per-seed analysis; the compact committed summary itself does not contain those median fields. The per-seed PCA mean values are the raw values in the pooled report. FAR-OO is not available as a named, well-defined per-seed metric in those summary files. No new results are claimed.


## 10. Additional source-level findings from the deeper hybrid-path audit

The following points were confirmed by reading the 4060 runner and shared routing implementation. They sharpen the experimental priorities above.

### 10.1 The LLM prompt does not consume the split's training examples

In `_generate_llm_formula`, the prompt is assembled from the equation description, domain, ordered variable names, and known constants. The answer-key field `metadata['ground_truth']` is explicitly excluded. The prompt does not include `X_train`, `y_train`, NN predictions, or a number of demonstrations selected from the current split.

**Implication:** if the same equation metadata and LLM request settings are used, changing the outer split should not directly change the textual LLM prompt. A change in LLM output across seeds is more likely to come from decoding/provider nondeterminism or a changed request context/configuration than from the smaller numerical training sample. However, the *hybrid decision and reported hybrid score* can change because the NN and covariate-dependent routing inputs change.

### 10.2 The current route is fail-closed to an ensemble, not a pure LLM route

The 4060 hybrid function sets `llm_degradation_delta = None` and status `not_calibrated`, with an explicit comment that the LLM-specific degradation cohort is not ready. The shared `route_decision_from_diagnostics` returns the ensemble route whenever either degradation delta or calibrated tau is unavailable. Therefore, with the current code path, a passing formula trust gate and no structural-risk token still do not select a pure-LLM route: the route reason is `degradation_probe_or_tau_unavailable`.

The code does run `_extrapolation_probe(X_train, y_train)`, but that probe trains an NN on a core subset of outer training data and evaluates on the training-edge subset. It is an **NN degradation diagnostic**, not an LLM-formula degradation estimate; its result is recorded separately and is not passed as `llm_degradation_delta`.

**Implication:** a reported hybrid score cannot be interpreted as the LLM's standalone symbolic-recovery performance. The experiment should report formula generation and trust-gate outcomes separately from the final ensemble/fallback predictor.

### 10.3 The NN has an internal edge-validation and abstention policy

The current MLP is `[128, 64, 32]` with LayerNorm and SiLU and no Dropout (the source comment says Dropout was omitted because training samples are few). Adam is created with learning rate 0.001 and no explicit weight decay argument. Early stopping uses a 20%-of-outer-train directional edge validation subset, patience 30, and the best validation checkpoint.

Two Ridge candidates are evaluated on the same edge-validation rows: positive-domain log-Ridge (`alpha=1.0`) and signed-feature Ridge (`alpha=1.0`). If the best Ridge edge score beats `max(0, NN edge R²)`, the MLP is rejected in favour of that Ridge candidate. If the NN edge R² is nonfinite or negative and no Ridge wins, the model abstains to the training-mean predictor.

**Implication:** “NN performance” in the saved arm is not necessarily the MLP's performance. It may be log-Ridge, signed Ridge, or a training-mean fallback. The report must separate raw MLP predictions/metrics from the selected NN-arm predictor and record selection frequency by sample size. The low-data study should test weight decay, dropout, smaller networks, and validation strategy, but also treat the Ridge/mean fallback policy as a separate factor.

### 10.4 Hybrid output can be an ensemble or NN replacement, not a recovered formula

When the formula passes the training trust gate, the current unavailable degradation calibration causes the ensemble route. The ensemble uses a query-wise weight based on KDE OOD probability computed from training covariates and test/query covariates: (w_{LLM}=0.3+0.7p_{OOD}), with the NN receiving the complement. If the NN arm abstains, the code selects its replacement predictor and does not blend the rejected MLP output.

If the formula fails the trust gate, the route is NN; the final score can then be from the NN, Ridge, or training mean. If the LLM formula route is selected in a future calibrated configuration, it evaluates the generated formula directly. The present configuration's unavailable LLM degradation delta makes that pure-LLM branch unavailable under the shared route policy.

**Implication:** add an explicit per-case field identifying the final predictor source (LLM formula / LLM-NN blend / MLP / log-Ridge / signed Ridge / training mean), and count formula trust-gate pass rates separately. A single hybrid (R^2) obscures these distinct outcomes.

### 10.5 Covariate-only access to the held-out query set

The OOD KDE is fitted using (X_{train}), then scores (X_{test}) covariates to set per-query blend weights. It does not use (y_{test}) for that weighting. This is not target leakage, but it is a transductive/query-covariate-aware evaluation policy. The PCA split is also explicitly described in its disclosure as transductive.

**Implication:** distinguish (a) inductive evaluation, where prediction for each query uses only the training-fitted model and query row, from (b) transductive batch evaluation, where the distribution of the whole query covariate set influences blend weights. Report both if deployment conditions do not guarantee access to the complete query batch.

### 10.6 Highest-priority concrete tests following this audit

1. **Formula-generation repeatability:** replay identical equation metadata and identical LLM settings over multiple calls; compare formula hashes and exact request provenance. No training rows are in the prompt, so this isolates LLM/provider variation.
2. **Formula-only rescoring:** evaluate each saved formula on the same saved train/test arrays, bypassing route selection and NN blending. Report train/test predictive scores and symbolic equivalence separately.
3. **Route decomposition:** for each case, tabulate formula present, parse/evaluation success, trust-gate pass/rejection reason, structural-risk flags, route reason, OOD weights, selected NN submodel, abstention, and final predictor source.
4. **MLP-versus-selected-NN comparison:** preserve raw MLP predictions before Ridge/mean substitution and compare their learning curves with the selected NN-arm output.
5. **Nested probe accounting:** record `n_fit` and `n_edge` for the NN extrapolation probe. It consumes only outer training data, but at small outer training sizes it may become unavailable (`n < 20`) or too small to provide a stable diagnostic.
6. **Inductive-versus-transductive OOD weighting:** compare per-query weights derived from a fixed training-only calibration reference with weights derived from the complete held-out query batch.
7. **Exact split manifests:** persist stable row IDs for outer train/test and NN fit/validation, plus the probe core/edge indices. This will make any future hidden-split concern directly auditable.

These findings do not prove that the LLM is the source of the performance gap. They show that the final hybrid metric currently mixes formula quality, NN quality, an NN abstention policy, OOD-weighted blending, and route availability. The next benchmark should expose these components rather than treating the hybrid as one opaque method.
