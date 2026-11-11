# Manuscript-aligned HypatiaX pipeline route

Status: implementation map for `promotion/rerun-code-review`; this document does not certify scientific results or authorize a run.

## 1. Keep the two routes separate

The manuscript describes (A) the per-task HypatiaX formula-discovery/routing algorithm and (B) the campaign-level benchmark schedule. A benchmark launcher stage is not itself one of the five routing stages. Do not conflate them.

## 2. Per-task five-stage routing algorithm

For each equation/task, the intended sequence in the main manuscript, Section 7.3, is:

1. **Trust gate.** Evaluate the proposed LLM expression on training data. Accept only if training R² >= 0.5 and predictions are numerically valid (finite; no NaN/Inf or division-by-zero). If rejected, route to neural fallback.
2. **Transcendental-token diagnostic.** Flag expressions containing exp, log, Phi, sin, cos, or erf. The manuscript says this flag indicates elevated structural complexity and activates ensemble mode.
3. **LLM boundary-degradation probe.** Evaluate the *LLM-proposed formula* on the training rows and on the upper 20% of training samples ordered by projection onto the first PCA direction. Compute Delta = R²_LLM,train - R²_LLM,edge. Compare with a domain-calibrated threshold tau. Delta > tau activates ensemble mode. This is not an NN-fit degradation probe; the manuscript does not define Stage 3 as comparing NN core-fit and edge-fit R².
4. **OOD diagnostic.** Fit the KDE on training projections and estimate OOD likelihood for the query/input locations. This must not use held-out target labels or held-out scores. High p_OOD increases the LLM weight.
5. **Final route and blend.** The manuscript specifies neural fallback for a failed trust gate; pure LLM for training R² >= 0.95 and Delta <= tau; otherwise ensemble for a trusted candidate. For ensemble mode, w_LLM = alpha + (1-alpha)*p_OOD, w_NN = 1-w_LLM, alpha=0.3; blend the LLM and neural predictions.

All paths converge to one selected formula/prediction record. Store the proposed formula, parsed formula, selected route, every diagnostic value, thresholds, blend weights, and failure status.

### Manuscript consistency issue — agreed precedence and implementation status

**Decision agreed:** the structural-risk flag takes precedence over the high-fit pure-LLM shortcut. In the DeFi LLM+NN route, a trusted formula containing a flagged function is sent to the ensemble even when training R² >= 0.95. In Core-15 HDS v50_2, which has no NN component, the equivalent guard skips pure-LLM acceptance and forces PySR refinement; it must not be described as an LLM+NN ensemble.

**Implemented on this branch:**
- `hypatiax/core/routing.py` detects exact calls to exp/log/Phi/sin/cos/erf and implements a training-fitted 1-D PCA/KDE OOD tail score plus the manuscript blend (w_{LLM}=0.3+0.7p_{OOD}).
- The authoritative DeFi benchmark, `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py`, implements a *different* NN-based central-versus-tail probe (15% total tails) and training-fitted KDE/blending. This is not the manuscript's stated Core-15 Stage 3, which probes the LLM formula on the upper 20% of training rows. Treat this as a protocol/code discrepancy, not evidence that the Core-15 probe is implemented.
- `HYPATIAX_ROUTING_DELTA_TAU` must be supplied from a separate training-only calibration. If tau is absent/invalid, the route fails closed to ensemble; the fresh runner clears any inherited value when config tau is null.
- The legacy `hybrid_system_nn_defi_domain.py` path now fits a separate NN on the central training rows for its edge probe (rather than scoring edge rows with the full-fit NN); it uses the same standardized symmetric split and training-fitted KDE when `X_query` is supplied. `test_hybrid_nn_routing_probe.py` checks that the probe fit excludes both edge tails. `test_enhanced_defi_extrapolation.py` passes held-out covariates only and removes the old post-hoc overrides that could force pure LLM.
- `symbolic_engine.py` applies structural-risk precedence to the Core-15 HDS v50_2 LLM-acceptance shortcut. Since that architecture is LLM+PySR rather than LLM+NN, it forces PySR refinement instead of claiming an NN ensemble. The flag/tokens/reason are propagated into `exp1_ablation.py` rows.
- Regression tests cover exact token detection, structural-risk precedence, the training-edge probe, KDE OOD ordering, per-query blend weights, missing tau, and NN-unavailable fallback. The tests have been added but not executed.

**Still open:** `tau` has no manuscript-specified calibrated numeric value or frozen calibration dataset/procedure. Do not set it by looking at extrapolation/test scores. The manuscript's Core-15 Stage 3 is an LLM-formula probe on the upper 20% of training rows ordered by the first PCA projection; the current DeFi code's NN central-versus-tail probe is a distinct implementation and must not be substituted. The Core-15 paper also specifies a residual MLP (three Linear→LayerNorm→SiLU→Linear residual blocks), Adam at 1e-3 with weight decay 1e-4, augmentation `(X,y) ∪ (1.2X,1.2y)`, and an additional LLM-prediction input feature for hybrid neural fallback. The isolated `core15_nn.py` MLPRegressor helper does not match that architecture and is not a manuscript-faithful Core-15 NN. It remains experimental scaffolding only; its PCA edge splitter also does not implement the manuscript's LLM upper-20% probe. A second historical candidate, `hypatiax/core/training/baseline_neural_network_defi_improved.py`, is also not a drop-in match: it uses an input projection followed by a configurable sequence of hidden-width transitions (the local fallback defaults to [128,64,32] for up to two inputs and other widths for larger inputs), AdamW rather than the specified Adam, adaptive log transforms/scaling, validation-based early stopping, learning-rate scheduling, and multi-seed restarts. Its `ImprovedNN` block is Linear→LayerNorm→SiLU plus a skip, not the paper's stated Linear→LayerNorm→SiLU→Linear residual block; its default five-width configuration creates four transitions, not three specified blocks. It is a DeFi-oriented adaptive baseline, not evidence that the Core-15 residual MLP is implemented. Reusing it would silently change both architecture and training protocol. Core-15 HDS v50_2 still lacks the residual NN, query-time LLM/NN prediction fusion, and calibrated tau needed for a genuine six-gate leave-one-out study. Only LLM acceptance, structural-risk complexity routing, and PySR prior are switchable in the Phase 3 harness. The symbolic engine does preserve the raw LLM candidate (`llm_best_expression`) and its training score (`llm_best_r2`) in its hybrid result metadata, so a future implementation can evaluate that independent candidate on the specified training edge subset without another LLM call. However, `HybridDiscoverySystem.discover()` and `exp1_ablation.run_condition()` do not currently produce the residual-NN and blended predictions or score them under the benchmark contract. The Phase 3 adapter must continue rejecting these three arms. Before integration, specify and test the residual MLP's exact block widths, skip projection for input/output width changes, training epochs/stopping rule, augmentation semantics for multivariate variables, LLM candidate evaluation in original units after HDS log transforms, and output-schema/provenance fields. Keep all arms on identical training splits, seeds, evaluator, and resource accounting. The supplementary report's global `Complete Hyperparameter Specifications for All Methods` table separately lists a generic Neural Network as `[64, 32, 1]`, ReLU, Adam at 0.01, full-batch 160 samples, 200 epochs, Xavier uniform, and no dropout. It is not explicitly labelled as the Core-15 residual MLP, and conflicts with the main-text residual architecture/optimizer settings if interpreted as that model. The Core-15 appendix subsection reports outcome statistics but supplies no Core-15-specific training recipe. Therefore do not import the generic table's settings into the residual MLP implementation; resolve this manuscript-level ambiguity against the authors' experiment configuration or source run artifacts before claiming faithful reproduction. A further repository candidate, `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py`, does re-evaluate LLM formulas and obtains NN predictions for a post-hoc blend, but its NN is a plain Sequential stack of Linear→LayerNorm→SiLU layers (adaptive widths), trained with AdamW at 3e-3 and a validation/scheduler/early-stop loop. The LLM prediction is kept as a separate blend stream rather than appended as an input feature to the NN. Thus it demonstrates reusable formula-evaluation/blending patterns, not the manuscript's residual architecture or LLM-augmented neural fallback. It must not be presented as Core-15 faithful.


### Core-15 five-system benchmark is a separate comparison, not the six-gate HDS ablation

The campaign's `exp1_five_system.py` imports five method wrappers from `run_comparative_suite_benchmark_v2.py` (registry indices 1, 2, 4, 5, 6). Its “Neural Network” row is `ImprovedNNMethod`, which wraps the DeFi-oriented `baseline_neural_network_defi_improved.ImprovedNN`; it is not the manuscript's specified three-block Core-15 residual MLP. The wrapper uses a deterministic description-derived seed when `nn_seeds=1`, an internal 80/20 split for model/fallback selection, adaptive log-space transformations and fallback logic, and then reports its headline R² against the full supplied `X,y` arrays. In `exp1_five_system.py`, those arrays are the 160-row training set generated from the Core-15 equation. Therefore its headline neural R² is an in-sample training score, not a held-out validation score and not directly comparable to a held-out metric. The wrapper separately computes `r2_heldout`/`rmse_heldout` on its internal 20% validation split, but `exp1_five_system.py` does not copy those metadata fields into its returned row; it serializes `result.r2` as `train_r2`. That held-out diagnostic is discarded by this adapter. The internal split is made from the 160 rows passed by the adapter (128 fit rows and 32 validation rows), while the adapter's outer 40-row `X_test, y_test` from the 200-row generator are not passed to the method. More importantly, the NN wrapper uses that same internal validation split to choose among the NN, log-OLS, and linear-NN fallback candidates, then reports `r2_heldout` on it; this is a model-selection set, not an untouched final test set, so even the separately computed held-out diagnostic is selection-biased and must not be presented as an unbiased generalisation estimate. The wrapper's headline metric is recomputed on all 160 supplied rows after selecting the model, so it is explicitly in-sample. The outer `X_test,y_test` returned by `generate_data()` are not passed to the method or used in the five-system row. The separate near/medium/far scores are evaluated on extrapolation arrays. Preserve these metric meanings in tables and labels.

The five-system “System 3 LLM+Fallback” row wraps the all-domains hybrid, while “Hybrid v50_2” calls the subprocess-based PySR path without the LLM proposal step. The latter is explicitly a different call path from the LLM-enabled `HybridDiscoverySystem.discover()` used by the two-condition `exp1_ablation.py` “hypatia” condition. These five-system rows are not the Core-15 six-gate leave-one-out arms and must not be represented as such.

The repository also contains committed historical `five_systems/exp1_five` outputs, including a run log and provenance map dated 2026-08-12. They record an earlier execution (the log reports an API key was present) and are not evidence that the current promotion-branch code/config has passed a fresh rerun. Keep them clearly separated from fresh campaign outputs; do not reuse them as current-run results or silently overwrite/merge them into a fresh result namespace.

The manuscript's Stage 3 probe evaluates the LLM formula on the upper 20% of training rows ordered by the first PCA projection; it does not fit an NN on a central subset for this diagnostic. Stage 4 fits PCA/KDE and reference densities using training covariates only. Query covariates may be scored without labels. Held-out target labels/scores must never select the route, tune tau, or choose blend weights.

## 3. Campaign-level experiment route

Run each campaign into its own fresh output namespace. Keep splits, denominators, thresholds, and method arms separate.

| Order | Campaign | Manuscript protocol / required interpretation |
|---|---|---|
| 0 | Preflight and integrity | Environment/dependency checks; ground-truth prompt leak guard; clean checkout; fresh empty output; record commit, config, model, temperature, seeds, dependencies, and run manifest. |
| 1 | DeFi v3.0 | 74 tasks; primary fresh protocol specifies PCA-directed 40/60. Report training/in-distribution and held-out extrapolation separately. Keep random and PCA split results distinct. |
| 2 | DeFi portfolio robustness | Five-seed portfolio variance sweep (42, 99, 123, 777, 2024) and the separately labelled random-holdout/bootstrap/PCA-tail/feature diagnostics. |
| 3 | Core-15 controlled comparison | 15 fixed equations; near (1.2x), canonical, and far (5x) extrapolation. The manuscript's decision-aligned plan requires Pure LLM, full HDS v50_2, and six leave-one-gate-out arms: LLM acceptance, probe, complexity routing, NN augmentation, blend weight, and PySR prior. |
| 4 | Feynman five-system exp1 | Core-15 comparison suite; report each method and extrapolation metric separately. Do not substitute the Core-15 PySR-only ablation for the six-gate controlled study. |
| 5 | Feynman 10-domain exp2 | Separate 10-domain suite. Keep interpolation and extrapolation denominators distinct; where finite held-out extrapolation scores are absent, report no comparison. |
| 6 | Nguyen-12 | 12 standard equations; per-equation axis-aligned train/extrapolation ranges; 40/60; five seeds (42, 99, 123, 777, 2024); HypatiaX vs PySR-only. Use the manuscript's R² >= 0.9999 convention, count aborts/missing/NaN as failures, and disclose that no NN baseline is specified. |
| 7 | Protocol-30 | **Wired; not yet executed.** `Protocol30` adapts the manuscript-linked `_build_feynman_equations()` source registry into an explicit custom-protocol identity: 30 analytic equations across biology, chemistry, electrochemistry, electromagnetism, electrostatics, magnetism, mechanics, optics, probability, quantum, and thermodynamics. The fresh launcher now has separate six-method random 80/20 and PCA 40/60 stages, both noiseless with threshold R² >= 0.999999. The PCA-held-out 60% is the extrapolation evaluation set. The 10-domain `ExperimentProtocolAll` registry remains a separate proxy. |
| 8 | M3/M4 noise sweep | Same custom 30 equations, n=200, sigma in {0, 0.05, 0.1, 0.5, 1}%. Preserve the threshold used at each noise level in the raw data and caption; because thresholds vary, do not compare recovery percentages as if they shared one threshold. |
| 9 | M3/M4 sample-complexity sweep | Same 30 equations, noiseless, n in {50, 100, 200, 500, 750, 1000}; preserve the sample-size-specific thresholds. |
| 10 | Post-run audit | Verify formulas, LLM-call flags, hardcoded/hint bypass flags, seeds, split hashes, raw and scored R², finite/missing status, timeout status, runtime, resource use, and exact evaluator version. Generate manuscript tables/figures only from the audited fresh outputs. |

### Important benchmark distinctions

- DeFi's 74-task PCA 40/60 campaign, Core-15, 10-domain all-domains proxy, Nguyen-12, and custom Protocol-30 are different suites.
- Nguyen-12 is axis-aligned, not PCA-directed.
- Protocol-30 is a custom 30-equation suite, not a subset of AI Feynman.
- PureLLM historical Protocol-30 results include 11 hardcoded/fitted bypass rows. The fresh launcher disables hardcoded formulas and prompt hints; new results must be labelled as the clean live path, not spliced into historical tables without a full rerun of all comparison arms.
- The five-system exp2_five suite does not replace Protocol-30.
- Instability Index/stochastic regime-distribution results are not part of the current primary fresh route; the main paper explicitly says it reports single-run results only. Treat instability as a separately designed future campaign.

## 4. Current promotion launcher mapping

The current `ci_runner/run_fresh_experiments.sh` stage list is:

`env_check → gt_leak_guard → exp1 → exp1b → portfolio → portfolio_random_holdout → portfolio_bootstrap_pca → portfolio_feature_ranking → portfolio_pca_tail_error → exp1_ablation → exp1_ablation_aggregate → exp1_five → exp1_pca → exp1b_pca → extrap → hybrid_all_domains → exp2_feynman → exp2_feynman_pca_4060 → exp2_feynman_extrap → exp2_protocol30_random_8020 → exp2_protocol30_pca_4060 → exp2 → exp2_five → exp3 → exp3b → suppA → suppB → suppB_sc`

Interpretation and gaps:

- `exp1` / `exp1_pca`: DeFi benchmark paths; `exp1b` / `exp1b_pca` are DeFi seed/portfolio paths.
- `exp1_ablation` currently advertises only PySR-only, HypatiaX, and HypatiaX-noLLM. It does **not** implement the six leave-one-gate-out arms in the main paper's decision-aligned plan. Do not label the existing three-way comparison as a six-gate ablation.
- `exp1_five` is the Core-15 five-system comparison; it is not the full six-gate ablation.
- `exp2_five` is the separate 10-domain five-system comparison.
- `exp3` and `exp3b` are Nguyen-12 seed 42 and additional seeds.
- `suppB` and `suppB_sc` are the M3/M4 noise and sample-complexity sweeps.
- `exp2_protocol30_random_8020` and `exp2_protocol30_pca_4060` use the manuscript-linked custom 30-equation registry through the new `Protocol30` adapter. They are separate output namespaces and use all six methods, noiseless data, and the paper's strict 0.999999 threshold. The PCA route uses 40% training / 60% held-out.
- `exp2` and `exp2_five` continue to run the distinct 10-domain `ExperimentProtocolAll` proxy. The optional `exp2_all_domains_pca_4060` proxy stage remains deferred. Never combine proxy outputs with Protocol-30 results.
- The config marks instability as disabled/deferred, consistent with the manuscript's single-run limitation.

## 5. Supplementary-protocol correction required

The Supplement B sweep-design table currently states that the sample-complexity sweep fixes sigma=5%, but the same supplement's sample-complexity results and raw-data description say it is **noiseless**. The run protocol and manuscript table must be reconciled; the sample-complexity sweep should be documented as noiseless if that is what the source files establish.

The noise-sweep recovery thresholds vary by sigma (0.999999 at 0%; 0.995 at 0.05%, 0.1%, and 0.5%; 0.99 at 1%). Those are valid source-defined thresholds but are not a common recovery scale. Always show the threshold beside each row.

## 6. Safe execution and acceptance gates

The fresh launcher requires a new empty RESULTS_DIR outside the repository, a clean Git checkout, no legacy mode, and records a run manifest. It forces hardcoded-formula and prompt-hint bypasses off and clears inherited LLM cache/replay settings. The real route includes a live API preflight and a PySR warm-up; do not execute it without explicit approval of compute/API spend.

Before any scientific run:
- Calibrate and freeze the Stage 3 degradation threshold tau using a separate training-only calibration protocol; tau is currently intentionally unset by default.
- Complete Core-15 gate ablations only where the underlying gates are genuinely implemented in the Core-15 architecture. The Phase 3 harness now wires LLM acceptance, structural-risk complexity routing, and PySR prior. Neural degradation probe, NN augmentation, and blend weight still require the separate DeFi LLM+NN architecture and are not HDS v50_2 switches. Do not call this a completed six-gate study.
- Verify the two new Protocol-30 routes and output schemas after the user runs the fresh campaign. Historical 2026-08-12 Protocol-30 outputs are marked contaminated (11 bypass rows) and must not be mixed with the new clean runs.
- Audit the R² evaluator's total-sum-of-squares guard, including near-constant targets.
- Pin/report the actual runtime LLM model and temperature behavior for every call path (including whether the SDK sends a temperature parameter).
- Confirm each campaign's output schema records exact formula, route, LLM-call flag, seed, split, failure status, timing, raw/scored R², and evaluator output.

No experiment is run by this documentation change.
