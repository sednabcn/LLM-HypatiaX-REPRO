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
5. **Final route and blend.** The manuscript specifies neural fallback for a failed trust gate; pure LLM for training R² >= 0.95 and Delta < tau; otherwise ensemble for a trusted candidate. For ensemble mode, w_LLM = alpha + (1-alpha)*p_OOD, w_NN = 1-w_LLM, alpha=0.3; blend the LLM and neural predictions.

All paths converge to one selected formula/prediction record. Store the proposed formula, parsed formula, selected route, every diagnostic value, thresholds, blend weights, and failure status.

### Manuscript consistency issue — agreed precedence and implementation status

**Decision agreed:** the structural-risk flag has precedence over the high-fit pure-LLM shortcut. A trusted candidate using a flagged function is routed to an LLM+NN ensemble even when training R² >= 0.95. A failed trust gate routes to NN fallback. Pure LLM is eligible only when the trust gate passes, no structural-risk function is present, and training R² >= 0.95.

**Implemented on this branch (scoped):** `hypatiax/core/routing.py` provides exact function-call detection for exp/log/Phi/sin/cos/erf and a deterministic route selector. `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py` now uses it in the EnhancedHybridSystem DeFi route, logs the route reason, and returns trust-gate status, structural-risk flag/tokens, and blend weights. Regression tests cover exact-call detection, formula-fragment fallback, high-fit structural-risk override, high-fit non-structural pure LLM, and trust-gate failure. This is **not yet wired into the separate Core-15 `exp1_ablation.py` / `HybridDiscoverySystem v50_2` route**; that path remains a separate integration task.

**Still not implemented:** end-to-end application to the Core-15 v50_2 path; the manuscript's Stage 3 training-side edge degradation probe and calibrated tau; Stage 4 training-fitted KDE/OOD probability; and the manuscript's specified alpha=0.3 OOD-dependent blend formula. The current helper deliberately retains the existing R²-proportional blend for compatibility and does not claim those missing stages are complete. These remain pre-run blockers for claiming full five-stage algorithm conformance.

The Stage 3 edge probe must be drawn from training data. Stage 4 may use only unlabelled query covariates plus training-fitted density information. Never use held-out target labels/scores to select a route, tune tau, or choose blend weights.

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
| 7 | Protocol-30 | Dedicated custom 30-equation benchmark across 11 domains; not a Feynman subset. Preserve random 80/20 and PCA 40/60 as separate protocols. For PCA, only the held-out 60% score is the extrapolation measure. Use the paper's strict R² >= 0.999999 criterion and retain formula strings for audit. |
| 8 | M3/M4 noise sweep | Same custom 30 equations, n=200, sigma in {0, 0.05, 0.1, 0.5, 1}%. Preserve the threshold used at each noise level in the raw data and caption; because thresholds vary, do not compare recovery percentages as if they shared one threshold. |
| 9 | M3/M4 sample-complexity sweep | Same 30 equations, noiseless, n in {50, 100, 200, 500, 750, 1000}; preserve the sample-size-specific thresholds. |
| 10 | Post-run audit | Verify formulas, LLM-call flags, hardcoded/hint bypass flags, seeds, split hashes, raw and scored R², finite/missing status, timeout status, runtime, resource use, and exact evaluator version. Generate manuscript tables/figures only from the audited fresh outputs. |

### Important benchmark distinctions

- DeFi's 74-task PCA 40/60 campaign, Core-15, Feynman 10-domain, Nguyen-12, and custom Protocol-30 are different suites.
- Nguyen-12 is axis-aligned, not PCA-directed.
- Protocol-30 is a custom 30-equation suite, not a subset of AI Feynman.
- PureLLM historical Protocol-30 results include 11 hardcoded/fitted bypass rows. The fresh launcher disables hardcoded formulas and prompt hints; new results must be labelled as the clean live path, not spliced into historical tables without a full rerun of all comparison arms.
- The five-system exp2_five suite does not replace Protocol-30.
- Instability Index/stochastic regime-distribution results are not part of the current primary fresh route; the main paper explicitly says it reports single-run results only. Treat instability as a separately designed future campaign.

## 4. Current promotion launcher mapping

The current `ci_runner/run_fresh_experiments.sh` stage list is:

`env_check → gt_leak_guard → exp1 → exp1b → portfolio → portfolio_random_holdout → portfolio_bootstrap_pca → portfolio_feature_ranking → portfolio_pca_tail_error → exp1_ablation → exp1_ablation_aggregate → exp1_five → exp1_pca → exp1b_pca → extrap → hybrid_all_domains → exp2_feynman → exp2_feynman_pca_4060 → exp2_feynman_extrap → exp2 → exp2_five → exp3 → exp3b → suppA → suppB → suppB_sc`

Interpretation and gaps:

- `exp1` / `exp1_pca`: DeFi benchmark paths; `exp1b` / `exp1b_pca` are DeFi seed/portfolio paths.
- `exp1_ablation` currently advertises only PySR-only, HypatiaX, and HypatiaX-noLLM. It does **not** implement the six leave-one-gate-out arms in the main paper's decision-aligned plan. Do not label the existing three-way comparison as a six-gate ablation.
- `exp1_five` is the Core-15 five-system comparison; it is not the full six-gate ablation.
- `exp2_five` is the separate 10-domain five-system comparison.
- `exp3` and `exp3b` are Nguyen-12 seed 42 and additional seeds.
- `suppB` and `suppB_sc` are the M3/M4 noise and sample-complexity sweeps.
- There is no dedicated Protocol-30 stage in this launcher. Do not claim that Protocol-30 is freshly rerun by `exp2` or `exp2_five`. This remains a pre-run blocker; no stage is added until the custom 30-equation source, clean live method arms, random/PCA split definitions, output schema, and timeout policy are pinned.
- The fresh protocol currently contains no explicit Protocol-30 campaign entry. Add one only after its inputs, clean-path method arms, output schema, and timeout policy are frozen.
- The config marks instability as disabled/deferred, consistent with the manuscript's single-run limitation.

## 5. Supplementary-protocol correction required

The Supplement B sweep-design table currently states that the sample-complexity sweep fixes sigma=5%, but the same supplement's sample-complexity results and raw-data description say it is **noiseless**. The run protocol and manuscript table must be reconciled; the sample-complexity sweep should be documented as noiseless if that is what the source files establish.

The noise-sweep recovery thresholds vary by sigma (0.999999 at 0%; 0.995 at 0.05%, 0.1%, and 0.5%; 0.99 at 1%). Those are valid source-defined thresholds but are not a common recovery scale. Always show the threshold beside each row.

## 6. Safe execution and acceptance gates

The fresh launcher requires a new empty RESULTS_DIR outside the repository, a clean Git checkout, no legacy mode, and records a run manifest. It forces hardcoded-formula and prompt-hint bypasses off and clears inherited LLM cache/replay settings. The real route includes a live API preflight and a PySR warm-up; do not execute it without explicit approval of compute/API spend.

Before any scientific run:
- Complete and test the Stage 3 training-side degradation probe and Stage 4 train-fitted KDE/OOD weighting; the current routing patch only resolves trust-gate and structural-risk precedence.
- Add and validate the six Core-15 leave-one-gate-out arms; do not treat the current three-arm ablation as complete.
- Freeze and implement the dedicated Protocol-30 campaign inputs, arms, split definitions, schema, and timeout policy.
- Add a dedicated Protocol-30 stage with clean formula provenance.
- Implement the six Core-15 leave-one-gate-out variants, on the same equations/splits/seeds/resources as Pure LLM and full HDS.
- Audit the R² evaluator's total-sum-of-squares guard, including near-constant targets.
- Pin/report the actual runtime LLM model and temperature behavior for every call path (including whether the SDK sends a temperature parameter).
- Confirm each campaign's output schema records exact formula, route, LLM-call flag, seed, split, failure status, timing, raw/scored R², and evaluator output.

No experiment is run by this documentation change.
