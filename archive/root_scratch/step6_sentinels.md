# Step 6: non-finite sentinels

Convention to apply at every RESULT site: store `None` for the metric and a short `error` reason; never -inf/inf/nan.
`MethodResult(r2=None, rmse=None, error='<reason>')`; callers must use a None-safe test (`x is not None and np.isfinite(x)`).
INTERNAL sites (optimiser bounds, best-so-far trackers) can stay; mark them `# audit: ignore[M3]` once you confirm they never reach a result row.

| file | RESULT | INTERNAL |
|---|---|---|
| `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py` | 11 | 13 |
| `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py` | 11 | 13 |
| `scripts/close_phase1.py` | 6 | 3 |
| `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py` | 6 | 13 |
| `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py` | 6 | 12 |
| `hypatiax/tools/symbolic/hybrid_system_v50_2.py` | 4 | 1 |
| `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py` | 4 | 2 |
| `hypatiax/core/metrics.py` | 3 | 5 |
| `hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py` | 3 | 0 |
| `scripts/phase3_engine_adapter.py` | 2 | 0 |
| `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py` | 2 | 4 |
| `scripts/run_pure_llm_arm.py` | 1 | 3 |
| `hypatiax/protocols/experiment_protocol_benchmark_v2.py` | 1 | 0 |
| `hypatiax/protocols/experiment_protocol_nguyen12.py` | 1 | 2 |
| `hypatiax/experiments/benchmarks/exp1_ablation.py` | 1 | 0 |
| `hypatiax/experiments/benchmarks/extrap_r2_far.py` | 1 | 3 |
| `hypatiax/core/training/baseline_neural_network_defi_improved.py` | 1 | 5 |
| `hypatiax/core/generation/hybrid_defi_llm_nn/hybrid_ensemble_system_defi_domain.py` | 1 | 0 |
| `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py` | 1 | 3 |
| `exp1_llm_contribution.py` | 0 | 1 |
| `scripts/check_closure_nonfinite.py` | 0 | 5 |
| `scripts/migrate_r2_repro.py` | 0 | 1 |
| `scripts/phase2_close.py` | 0 | 1 |
| `hypatiax/core/r2_canonical.py` | 0 | 7 |
| `hypatiax/core/json_safe.py` | 0 | 1 |
| `hypatiax/tools/symbolic/smart_structure_detector.py` | 0 | 1 |
| `hypatiax/tools/symbolic/physics_aware_regressor.py` | 0 | 12 |
| `hypatiax/tools/symbolic/symbolic_engine.py` | 0 | 2 |
| `hypatiax/experiments/benchmarks/run_hybrid_system_benchmark.py` | 0 | 1 |
| `hypatiax/experiments/benchmarks/run_instability_suite.py` | 0 | 1 |
| `hypatiax/core/training/adaptive_config.py` | 0 | 4 |
| `hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py` | 0 | 2 |
| `.github/scripts/compute_solve_rate.py` | 0 | 1 |
| `scripts/tools/merge_instability_shards.py` | 0 | 1 |
| `scripts/ci/ablation_multiseed_summary.py` | 0 | 2 |

## RESULT sites

- `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py:837`  `llm_r2 = llm_metrics.get("r2", 0) if llm_metrics.get("success") else -np.inf`
- `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py:868`  `"rmse": float(llm_metrics.get("rmse", float("inf"))),`
- `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py:902`  `final_rmse = llm_metrics.get("rmse", float("inf"))`
- `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py:930`  `final_rmse = (llm_metrics.get("rmse", float("inf"))`
- `hypatiax/core/generation/hybrid_defi_llm_nn/hybrid_ensemble_system_defi_domain.py:303`  `llm_r2_tr = llm_r2_te = float("nan")`
- `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py:570`  `r = r2_score(y_train, p) if p is not None else -np.inf`
- `hypatiax/core/metrics.py:115`  `>>> compute_r2([1, 2, 3], [1, float("nan"), 3])`
- `hypatiax/core/metrics.py:383`  `assert compute_r2([1, 2, 3], [1, float("inf"), 3]) == float("-inf")`
- `hypatiax/core/metrics.py:388`  `compute_r2([1, float("nan")], [1, 2])`
- `hypatiax/core/training/baseline_neural_network_defi_improved.py:442`  `r2 = 1.0 if bool(np.allclose(y_pred, y, rtol=1e-9, atol=1e-30)) else float("-inf")`
- `hypatiax/experiments/benchmarks/exp1_ablation.py:724`  `train_rmse    = res.get("rmse", float("inf"))   # FIX-A: original-unit RMSE`
- `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py:1879`  `r2_h_report = r2_h_extrap if r2_h_extrap is not None else float("-inf")`
- `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py:1880`  `r2_p_report = r2_p_extrap if r2_p_extrap is not None else float("-inf")`
- `hypatiax/experiments/benchmarks/extrap_r2_far.py:51`  `ExtrapolationRegime("CATASTROPHIC", float("inf"), "≥ 500 % CATASTROPHIC"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:821`  `"train_r2":       float(llm_train_r2) if llm_train_ok else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:825`  `"llm_train_r2":   float(llm_train_r2) if llm_train_ok else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:1292`  `"train_r2": float(llm_tr_m["r2"]) if llm_tr_m.get("success") else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:1293`  `"test_r2":  float(llm_te_m["r2"]) if llm_te_m.get("success") else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:1363`  `tr_ = res.get("train_r2", float("nan"))`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:1364`  `te_ = res.get("test_r2",  float("nan"))`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:918`  `"train_r2":       float(llm_train_r2) if llm_train_ok else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:922`  `"llm_train_r2":   float(llm_train_r2) if llm_train_ok else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:1407`  `"train_r2": float(llm_tr_m["r2"]) if llm_tr_m.get("success") else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:1408`  `"test_r2":  float(llm_te_m["r2"]) if llm_te_m.get("success") else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:1480`  `tr_ = res.get("train_r2", float("nan"))`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:1481`  `te_ = res.get("test_r2",  float("nan"))`
- `hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py:324`  `'near_r2': r.get('near_r2', float('nan')),`
- `hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py:325`  `'medium_r2': r.get('medium_r2', float('nan')),`
- `hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py:607`  `'llm_train_r2': hybrid.get('llm_train_r2', float('nan')),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:196`  `ExtrapolationRegime("CATASTROPHIC", float("inf"), "≥ 500 % CATASTROPHIC"),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1037`  `r2=float("-inf"), rmse=float("inf"), formula="N/A", error=reason,  # PHASE1-FIX: failure, not a score`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1580`  `r2=float("nan"), rmse=float("inf"),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1595`  `rmse=float(metrics.get("rmse", float("inf"))),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:2536`  `rmse = float(rmse) if rmse is not None else float("inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:3139`  `rmse=float(result.get("rmse", float("nan"))),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:3297`  `rmse=float(result.get("rmse", float("nan"))),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:3492`  `r2=float("-inf"), rmse=float("inf"), formula="N/A",  # PHASE1-FIX: failure, not a score`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:3960`  `w_rmse  = wres.rmse if wres is not None else float("nan")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:4002`  `_rmse = mres.get("rmse", float("inf"))`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:4028`  `return float(np.nanmedian(r2s)) if r2s else float("-inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:176`  `ExtrapolationRegime("CATASTROPHIC", float("inf"), "≥ 500 % CATASTROPHIC"),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1073`  `r2=float("-inf"), rmse=float("inf"), formula="N/A", error=reason,  # PHASE1-FIX: failure, not a score`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1631`  `r2=float("nan"), rmse=float("inf"),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1646`  `rmse=float(metrics.get("rmse", float("inf"))),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:2608`  `rmse = float(rmse) if rmse is not None else float("inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:3374`  `rmse=float(result.get("rmse", float("nan"))),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:3536`  `rmse=float(result.get("rmse", float("nan"))),`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:3731`  `r2=float("-inf"), rmse=float("inf"), formula="N/A",  # PHASE1-FIX: failure, not a score`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:4218`  `w_rmse  = wres.rmse if wres is not None else float("nan")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:4260`  `_rmse = mres.get("rmse", float("inf"))`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:4286`  `return float(np.nanmedian(r2s)) if r2s else float("-inf")`
- `hypatiax/protocols/experiment_protocol_benchmark_v2.py:1420`  `if r.get("evaluation", {}).get("r2", -np.inf) >= threshold`
- `hypatiax/protocols/experiment_protocol_nguyen12.py:682`  `if r.get("evaluation", {}).get("r2", -np.inf) >= threshold`
- `hypatiax/tools/symbolic/hybrid_system_v50_2.py:1358`  `nrmse = float("nan")`
- `hypatiax/tools/symbolic/hybrid_system_v50_2.py:1507`  `nrmse = float("nan")`
- `hypatiax/tools/symbolic/hybrid_system_v50_2.py:1581`  `"nrmse": float("nan"),`
- `hypatiax/tools/symbolic/hybrid_system_v50_2.py:1689`  `rmse_ok = res_a["rmse"] < float("inf") and res_a["rmse"] >= 0`
- `scripts/close_phase1.py:139`  `assert compute_r2([1, 2, 3], [1, float("inf"), 3]) == float("-inf")`
- `scripts/close_phase1.py:144`  `compute_r2([1, float("nan")], [1, 2])`
- `scripts/close_phase1.py:670`  `assert metrics.compute_r2([1, 2, 3], [1, float("nan"), 3]) == float("-inf")`
- `scripts/close_phase1.py:671`  `assert metrics.compute_r2([1, 2, 3], [1, float("inf"), 3]) == float("-inf")`
- `scripts/close_phase1.py:676`  `metrics.compute_r2([1, float("nan")], [1, 2])`
- `scripts/close_phase1.py:725`  `assert metrics.compute_catastrophic_rate([0.9, float("nan"), float("-inf"), 0.5]) == 0.5`
- `scripts/phase3_engine_adapter.py:32`  `"llm_acceptance": ("_LLM_ACCEPT_R2", float("inf")),`
- `scripts/phase3_engine_adapter.py:208`  `"r2_raw": float(r2) if finite else float("-inf"),`
- `scripts/run_pure_llm_arm.py:1013`  `row["r2"] == float("-inf") and row["r2_status"].startswith("failed") and row["error_stage"] == "exec"`

## INTERNAL sites (review, then ignore)

- `.github/scripts/compute_solve_rate.py:282`  `rate = p / t if t else float("nan")`
- `exp1_llm_contribution.py:104`  `f"W/T/L {wins}/{ties}/{losses} | PRIMARY Wilcoxon p(>)={t.get('wilcoxon_p_greater', float('nan')):.4f} "`
- `hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py:782`  `"inf":     np.inf,`
- `hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py:783`  `"nan":     np.nan,`
- `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py:88`  `return (float(val) if ok else float("nan")), status`
- `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py:528`  `best_val   = float("inf")`
- `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py:130`  `best_loss  = float("inf")`
- `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py:403`  `else -np.inf`
- `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py:574`  `best_r2   = -np.inf`
- `hypatiax/core/json_safe.py:4`  `_DEC = {"NaN": float("nan"), "Infinity": float("inf"), "-Infinity": float("-inf")}`
- `hypatiax/core/metrics.py:205`  `>>> compute_near_perfect_rate([0.995, float("nan")], threshold=0.99)`
- `hypatiax/core/metrics.py:248`  `>>> compute_catastrophic_rate([0.9, float("nan"), float("-inf"), 0.5])`
- `hypatiax/core/metrics.py:250`  `>>> compute_catastrophic_rate([0.9, float("nan")], nan_as_failure=False)`
- `hypatiax/core/metrics.py:324`  `>>> m = evaluate_all([1, 2, 3], [1, float("nan"), 3])`
- `hypatiax/core/metrics.py:386`  `assert evaluate_all([1, 2, 3], [float("nan")] * 3)["catastrophic"] is True`
- `hypatiax/core/r2_canonical.py:57`  `return float("-inf"), "bad_shape"`
- `hypatiax/core/r2_canonical.py:59`  `return float("nan"), "degenerate_target"`
- `hypatiax/core/r2_canonical.py:61`  `return float("nan"), "nonfinite_target"`
- `hypatiax/core/r2_canonical.py:63`  `return float("-inf"), "nonfinite_pred"`
- `hypatiax/core/r2_canonical.py:68`  `return float("nan"), "degenerate_target"`
- `hypatiax/core/r2_canonical.py:97`  `return float("-inf"), "pred_out_of_range"`
- `hypatiax/core/r2_canonical.py:106`  `return float("-inf"), "catastrophic"`
- `hypatiax/core/training/adaptive_config.py:544`  `best_model, best_r2, best_train_loss = None, float("-inf"), float("inf")`
- `hypatiax/core/training/adaptive_config.py:545`  `best_score = float("-inf")`
- `hypatiax/core/training/adaptive_config.py:585`  `best_val   = float("inf")`
- `hypatiax/core/training/adaptive_config.py:588`  `final_train_loss = float("inf")`
- `hypatiax/core/training/baseline_neural_network_defi_improved.py:277`  `best_val         = float("inf")`
- `hypatiax/core/training/baseline_neural_network_defi_improved.py:280`  `final_train_loss = float("inf")`
- `hypatiax/core/training/baseline_neural_network_defi_improved.py:402`  `best_val_loss    = float("inf")`
- `hypatiax/core/training/baseline_neural_network_defi_improved.py:403`  `best_train_loss  = float("inf")`
- `hypatiax/core/training/baseline_neural_network_defi_improved.py:603`  `print(f"  Final Train Loss: {training.get('final_train_loss', float('nan')):.6f}")`
- `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py:546`  `return float("inf")`
- `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py:553`  `best_loss = float("nan")`
- `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py:557`  `best_complexity = float("nan")`
- `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py:1026`  `best_r2 = -np.inf`
- `hypatiax/experiments/benchmarks/extrap_r2_far.py:203`  `"inf": np.inf,`
- `hypatiax/experiments/benchmarks/extrap_r2_far.py:204`  `"nan": np.nan,`
- `hypatiax/experiments/benchmarks/extrap_r2_far.py:302`  `Returns float("-inf") when R² < -100 (pathological divergence).`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:366`  `return np.log(np.where(K > 0, S / K, np.nan))`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:377`  `"log":     lambda x: np.log(np.where(np.asarray(x) > 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:378`  `"log2":    lambda x: np.log2(np.where(np.asarray(x) > 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:379`  `"log10":   lambda x: np.log10(np.where(np.asarray(x) > 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:380`  `"sqrt":    lambda x: np.sqrt(np.where(np.asarray(x) >= 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:476`  `return float("nan"), False`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:662`  `"np.inf", "1/0", "**1000" are unambiguous — substring match is fine.`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:668`  `unambiguous = ["1/0", "np.inf", "**1000"]`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:704`  `if has_formula else (float("nan"), False)`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:1033`  `"median":        float(np.median(clipped)) if len(clipped) else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:1034`  `"mean_clip":     float(np.mean(clipped))   if len(clipped) else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py:1371`  `else float("nan")`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:81`  `- _formula_has_pathological_behavior() checks for "1/0", "np.inf",`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:460`  `return np.log(np.where(K > 0, S / K, np.nan))`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:471`  `"log":     lambda x: np.log(np.where(np.asarray(x) > 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:472`  `"log2":    lambda x: np.log2(np.where(np.asarray(x) > 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:473`  `"log10":   lambda x: np.log10(np.where(np.asarray(x) > 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:474`  `"sqrt":    lambda x: np.sqrt(np.where(np.asarray(x) >= 0, x, np.nan)),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:570`  `return float("nan"), False`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:759`  `"np.inf", "1/0", "**1000" are unambiguous — substring match is fine.`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:765`  `unambiguous = ["1/0", "np.inf", "**1000"]`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:801`  `if has_formula else (float("nan"), False)`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:1152`  `"median":        float(np.median(clipped)) if len(clipped) else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:1153`  `"mean_clip":     float(np.mean(clipped))   if len(clipped) else float("nan"),`
- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py:1488`  `else float("nan")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:348`  `"inf": np.inf,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:349`  `"nan": np.nan,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:487`  `Returns float("-inf") when R² < -100 (pathological divergence).`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1098`  `"inf": np.inf,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1099`  `"nan": np.nan,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1276`  `best_loss, best_w, patience = float("inf"), None, 0`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1296`  `best_r2 = float("-inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1444`  `"inf": np.inf,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1445`  `"nan": np.nan,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:1796`  `best_loss = float("inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:2409`  `best_loss, best_w, patience = float("inf"), None, 0`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:2430`  `best_r2     = float("-inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py:2611`  `bl3, bw3, pat3 = float("inf"), None, 0`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:355`  `"inf": np.inf,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:356`  `"nan": np.nan,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:492`  `Returns float("-inf") when R² < -100 (pathological divergence).`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1134`  `"inf": np.inf,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1135`  `"nan": np.nan,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1316`  `best_loss, best_w, patience = float("inf"), None, 0`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1336`  `best_r2 = float("-inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1484`  `"inf": np.inf,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1485`  `"nan": np.nan,`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:1862`  `best_loss = float("inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:2499`  `best_loss, best_w, patience = float("inf"), None, 0`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:2520`  `best_r2     = float("-inf")`
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py:2716`  `bl3, bw3, pat3 = float("inf"), None, 0`
- `hypatiax/experiments/benchmarks/run_hybrid_system_benchmark.py:362`  `return dict(n=0, median=float("nan"), mean_clipped=float("nan"),`
- `hypatiax/experiments/benchmarks/run_instability_suite.py:394`  `return np.nan`
- `hypatiax/protocols/experiment_protocol_nguyen12.py:908`  `h_train    = ref.get("H_train", float("nan"))`
- `hypatiax/protocols/experiment_protocol_nguyen12.py:909`  `p_train    = ref.get("P_train", float("nan"))`
- `hypatiax/tools/symbolic/hybrid_system_v50_2.py:722`  `best_r2 = -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:162`  `self.best_fitness_ = -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:342`  `best_overall_fitness = -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:343`  `best_val_fitness = -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:388`  `valid = sum(1 for f in fitness_scores if f > -np.inf)`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:460`  `best_fitness = -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:1733`  `fitness_scores.append(-np.inf)`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:1755`  `return -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:1757`  `return -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:1761`  `return -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:1783`  `return -np.inf`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:1796`  `valid = [(i, f) for i, f in enumerate(fitness_scores) if f > -np.inf]`
- `hypatiax/tools/symbolic/physics_aware_regressor.py:1836`  `valid = [i for i, f in enumerate(fitness_scores) if f > -np.inf]`
- `hypatiax/tools/symbolic/smart_structure_detector.py:237`  `best_r2 = -np.inf`
- `hypatiax/tools/symbolic/symbolic_engine.py:1762`  `best_r2 = -np.inf`
- `hypatiax/tools/symbolic/symbolic_engine.py:3151`  `"error": float("inf"),`
- `scripts/check_closure_nonfinite.py:49`  `v = {"-inf": -math.inf, "-infinity": -math.inf, "inf": math.inf,`
- `scripts/check_closure_nonfinite.py:50`  `"infinity": math.inf, "nan": math.nan}.get(s)`
- `scripts/check_closure_nonfinite.py:60`  `if v == -math.inf:`
- `scripts/check_closure_nonfinite.py:62`  `if v == math.inf:`
- `scripts/check_closure_nonfinite.py:172`  `return sum(d.values()) / len(d) if d else float("nan")`
- `scripts/ci/ablation_multiseed_summary.py:41`  `return -math.inf if v is None else float(v)`
- `scripts/ci/ablation_multiseed_summary.py:69`  `f = lambda v: "-inf" if v == -math.inf else f"{v:.4f}"`
- `scripts/close_phase1.py:142`  `assert evaluate_all([1, 2, 3], [float("nan")] * 3)["catastrophic"] is True`
- `scripts/close_phase1.py:632`  `lines[i] = _ZERO.sub(lambda m: m.group(1) + 'float("-inf")', lines[i])`
- `scripts/close_phase1.py:720`  `for v in (0.99, 0.9899999, 1.0, float("nan"), float("-inf")):`
- `scripts/migrate_r2_repro.py:81`  `'    return float("-inf")',`
- `scripts/phase2_close.py:216`  `return sum(flags) / len(flags) if flags else float("nan")`
- `scripts/run_pure_llm_arm.py:605`  `NEG = float("-inf")`
- `scripts/run_pure_llm_arm.py:917`  `neg = float("-inf")`
- `scripts/run_pure_llm_arm.py:976`  `return float("-inf"), "non_finite_prediction"`
- `scripts/tools/merge_instability_shards.py:25`  `except (TypeError, ValueError): return float("nan")`
