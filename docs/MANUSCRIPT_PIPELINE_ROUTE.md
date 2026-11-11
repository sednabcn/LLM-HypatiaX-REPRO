# Manuscript-aligned HypatiaX pipeline route

Status: implementation map for `promotion/rerun-code-review`; this document does not certify scientific results or authorize a run.

## 1. Keep the two routes separate

The manuscript describes (A) the per-task HypatiaX formula-discovery/routing algorithm and (B) the campaign-level benchmark schedule. A benchmark launcher stage is not itself one of the five routing stages. Do not conflate them.

## 2. Per-task five-stage routing algorithm

For each equation/task, the intended sequence in the main manuscript, Section 7.3, is:

1. **Trust gate.** Evaluate the proposed LLM expression on training data. Accept only if training R² >= 0.5 and predictions are numerically valid (finite; no NaN/Inf or division-by-zero). If rejected, route to neural fallback.
2. **Transcendental-token diagnostic.** Flag expressions containing exp, log, Phi, sin, cos, or erf. The manuscript says this flag indicates elevated structural complexity and activates ensemble mode.
3. **Neural degradation probe.** Compute Delta = R²_train - R²_edge, where edge performance is measured on a training-side boundary/probe subset. Compare with a domain-calibrated threshold tau. Delta > tau activates ensemble mode.
4. **OOD diagnostic.** Fit the KDE on training projections and estimate OOD likelihood for the query/input locations. This must not use held-out target labels or held-out scores. High p_OOD increases the LLM weight.
5. **Final route and blend.** The manuscript specifies neural fallback for a failed trust gate; pure LLM for training R² >= 0.95 and Delta <= tau; otherwise ensemble for a trusted candidate. For ensemble mode, w_LLM = alpha + (1-alpha)*p_OOD, w_NN = 1-w_LLM, alpha=0.3; blend the LLM and neural predictions.

All paths converge to one selected formula/prediction record. Store the proposed formula, parsed formula, selected route, every diagnostic value, thresholds, blend weights, and failure status.

### Manuscript consistency issue — agreed precedence and implementation status

**Decision agreed:** the structural-risk flag takes precedence over the high-fit pure-LLM shortcut. In the DeFi LLM+NN route, a trusted formula containing a flagged function is sent to the ensemble even when training R² >= 0.95. In Core-15 HDS v50_2, which has no NN component, the equivalent guard skips pure-LLM acceptance and forces PySR refinement; it must not be described as an LLM+NN ensemble.

**Implemented on this branch:**
- `hypatiax/core/routing.py` detects exact calls to exp/log/Phi/sin/cos/erf and implements a training-fitted 1-D PCA/KDE OOD tail score plus the manuscript blend (w_{LLM}=0.3+0.7p_{OOD}).
- The authoritative DeFi benchmark, `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py`, now applies structural-risk precedence, trains the NN degradation probe on the central training region and scores both PCA-axis tails (15% total) drawn only from training rows, with feature standardisation fitted on training covariates; the edge fraction is read from the fresh protocol. It fits KDE on `X_train`, and applies per-query weights to `X_test` without using `y_test`. The probe edge fraction is 15%.
- `HYPATIAX_ROUTING_DELTA_TAU` must be supplied from a separate training-only calibration. If tau is absent/invalid, the route fails closed to ensemble; the fresh runner clears any inherited value when config tau is null.
- The legacy `hybrid_system_nn_defi_domain.py` path now fits a separate NN on the central training rows for its edge probe (rather than scoring edge rows with the full-fit NN); it uses the same standardized symmetric split and training-fitted KDE when `X_query` is supplied. `test_hybrid_nn_routing_probe.py` checks that the probe fit excludes both edge tails. `test_enhanced_defi_extrapolation.py` passes held-out covariates only and removes the old post-hoc overrides that could force pure LLM.
- `symbolic_engine.py` applies structural-risk precedence to the Core-15 HDS v50_2 LLM-acceptance shortcut. Since that architecture is LLM+PySR rather than LLM+NN, it forces PySR refinement instead of claiming an NN ensemble. The flag/tokens/reason are propagated into `exp1_ablation.py` rows.
- Regression tests cover exact token detection, structural-risk precedence, the training-edge probe, KDE OOD ordering, per-query blend weights, missing tau, and NN-unavailable fallback. The tests have been added but not executed.

**Still open:** `tau` has no manuscript-specified calibrated numeric value or frozen calibration dataset/procedure. Do not set it by looking at extrapolation/test scores. The Core-15 HDS v50_2 architecture still lacks the NN-specific degradation/augmentation/blending components required for a genuine six-gate leave-one-out study; only LLM acceptance, structural-risk complexity routing, and PySR prior are switchable in its Phase 3 harness. These three omissions are intentional hard stops, not no-op ablations: `phase3_engine_adapter.run_case()` rejects an attempt to disable an unmapped gate before its preflight can run. The Core-15 engine returns a selected LLM/PySR expression and predictions; it does not construct the independent NN model, central-vs-edge NN probe, or per-query NN/LLM blending outputs required by those arms. Adding boolean switches without those computations would create placebo arms and invalidate the leave-one-gate-out interpretation. To implement them honestly, Core-15 must first be extended with an NN predictor trained on the identical Core-15 training split, an independently switchable training-only edge probe, a separately switchable NN prediction/augmentation path, and an independently switchable blend calculation; all arms must share data hashes, seeds, evaluator, and resource accounting. Until then, keep the three gates omitted and do not report six-gate results.

The Stage 3 probe trains on a core subset of the training rows and scores a boundary subset drawn from those same training rows. Stage 4 fits standardisation, PCA, KDE bandwidth, and leave-one-out reference densities using only training covariates. Query covariates are scored without labels. Held-out target labels/scores must never select the route, tune tau, or choose blend weights.

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
