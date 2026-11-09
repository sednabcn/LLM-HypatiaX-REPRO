#!/usr/bin/env python3
"""Append the new audit findings to audit/LEDGER.csv (idempotent: skips ids already present).
Columns assumed: id,block,claim,affects,evidence,stage,status,action  (as in L06).
Default is a dry run; pass --write to modify the file. Review the diff before committing."""
import csv, sys, pathlib

P = pathlib.Path("audit/LEDGER.csv")
H = "hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py"
V2 = "run_comparative_suite_benchmark_v2.py"

ROWS = [
    ("L03", "B2", "bypass off in controlled comparison", "exp1 family; phase2_closure",
     "532 result files lack llm_source; 15 ablation LLM rows have llm_source None; local_fallback paths in hybrid_system_nn_defi_domain.py:973,991",
     "S1", "unaudited-all-existing-results", "rerun on master with B2 fields; wire 01_provenance_gate.py into phase2_closure and CI"),
    ("L06", "B4", "Fix 4 blend weight uses test info", H + ":907-923",
     "blend weights w_llm/w_nn = R2 on full y; NN trained on 80% of scored rows; nn_r2 evaluated on FULL dataset; audit did not touch these lines",
     "S1", "in-sample-confirmed", "disclose method 4 headline R2 as in-sample or score on held-out split; confirm caller passes X_train in extrap mode"),
    ("L32", "B2", "hybrid_predict llm_r2 None crash", H + ":837-838", "np.isfinite(None) raises TypeError when r2 is None",
     "S1", "open", "apply patch from 04_decision_logic_repro.py; add unit test"),
    ("L33", "B2", "nn_r2 nan falls through decision logic", H + ":896-957", "nan comparisons are False -> silent nn_fallback",
     "S1", "open", "explicit nan/None NN branch with reason"),
    ("L34", "B2", "NN failure path scores r2 0.0", H, "nn_result metrics r2 0.0 on failure",
     "S1", "open", "return None + reason like PHASE1-FIX"),
    ("L35", "B2", "_extract_eval fallthrough", V2 + " HybridAllDomainsMethod.run",
     "first sub-dict with finite r2 wins regardless of decision", "S1", "open", "select the sub-dict matching decision, fail if absent"),
    ("L36", "B2", "eval_.get(r2, 0.0) default", V2, "missing r2 becomes 0.0", "S1", "open", "fail on missing"),
    ("L37", "B2", "_unavailable returns -inf/inf", V2, "JSON -Infinity; conflicts with audit-M3 None convention", "S1", "open",
     "use None + reason"),
    ("L38", "B2", "exp1_ablation rmse default inf", "exp1_ablation.py:724", "res.get(rmse, inf)", "S1", "open", "None + reason"),
    ("L39", "B4", "FIX 3 force_llm for 5 Feynman domains", V2, "hand-tuned override added after Newton gravity R2=0.69",
     "S1", "disclose", "disclose in manuscript or run with it off as ablation"),
    ("L40", "B4", "Table 14 null policy", "scripts/ci/ablation_multiseed_summary.py",
     "None -> -inf; paired test uses equations with finite median in all arms", "S1", "documented",
     "report failed_cells and excluded_from_paired per arm; primary test is paired Wilcoxon+Holm, MWU is sensitivity only"),
    ("L41", "B4", "exp1_llm_contribution.py null policy", "exp1_llm_contribution.py:37-61",
     "drops non-finite rows; 7 field-name aliases", "S1", "open", "align with summary script or mark orphan"),
    ("L42", "B2", "R2 policy constants", "hypatiax/core/r2_canonical.py:42-47",
     "REL_TOL=1e-24, CATASTROPHIC_FLOOR=-100, PRED_ABS_LIMIT=1e100, sign flip off", "S1", "document",
     "state in manuscript; run 03_r2_policy_selftest.py on benchmark targets for fragile offsets"),
    ("L43", "B2", "sign flip controls", "run_all.sh", "STRICT/DISABLE flags exported; SIGN_FLIP only default-off", "S1", "open",
     "export SIGN_FLIP=0 and assert STRICT==1"),
    ("L44", "B4", "all_domains protocol ignores seed/noiseless", "hybrid_all_domains step", "ExperimentProtocolAll takes no seed",
     "S1", "disclose", "no seed or noise claims from this step"),
    ("L45", "B2", "three compute_extrap_r2_far copies", "v2 runner; PCA runner; extrap_r2_far.py",
     "all call r2_canonical; PCA mixes r2_checked and r2_scored", "S1", "open", "pick one canonical copy or add agreement test"),
    ("L46", "B2", "stale run_all.sh extrap warnings", "run_all.sh:196-217", "_EXTRAP_MODULE_AVAILABLE is constant True", "S1",
     "open", "delete stale warnings"),
    ("L47", "B2", "deleted analysis stack still called by run_all.sh", "run_all.sh:1973,2231,2300,2793",
     "merge_extrap_into_benchmark.py, check_symbolic_equivalence.py, analyze_hybrid_performance.py, scripts/patches/paper_targets.json missing (78e4244)",
     "S1", "open", "restore or remove calls; make missing REQUIRED inputs abort instead of [SKIP]/[WARN]"),
    ("L48", "B2", "three pipeline workflows coexist", ".github/workflows ci_pipeline_public/_repro/_validate.yml",
     "public still has run_analysis stage dispatching deleted ci_analysis.yml", "S1", "open", "pick one live workflow, delete the others"),
    ("L49", "B4", "ablation_paired.json no longer produced", "run_all.sh:1982; ci_pipeline_check.yml:283,822",
     "warning promises ci_analysis.yml will generate it; that workflow is deleted; checkpoint still expects the file", "S1", "open",
     "decide producer or drop from expected files"),
    ("L50", "B4", "table and figure generators deleted; audit_figures_tables is a no-op reporting all_ok True", "run_all.sh:4088",
     "audit_final_gate may count a vacuous pass; paper_targets.json missing so audit_paper cannot check claims", "S1", "open",
     "mark step SKIPPED not ok; restore generators elsewhere before claiming table consistency"),
    ("L51", "B2", "HYPATIAX_STRICT not asserted", "run_all.sh:54", "default-only export; STRICT=0 in shell would win", "S1", "open",
     "abort unless STRICT==1"),
    ("L52", "B2", "ablation LLM arm never records llm_source", "exp1_ablation.py; 38 ablation result files",
     "15 of 45 rows per file (the hypatia arm) have llm_called True and llm_source None", "S1", "open",
     "propagate llm_source into rows; rerun"),
    ("L53", "B4", "no held-out OOD score for method 4, Pure LLM, NN, System 3", "extrap_r2_far census",
     "HybridSystemLLMNN 150/150 None; ImprovedNN 150/150; System 3 30/30; PureLLM baseline 0 finite of 150", "S1", "open",
     "exclude from OOD claims or compute OOD for them"),
    ("L54", "B2", "PureLLM baseline r2 exactly 0.0", "05_null_census", "17 of 629 r2 values are 0.0 (failure-as-score signature)", "S1", "open",
     "trace rows; None + reason"),
    ("L55", "B4", "core15_instability extrap_r2_far", "05_null_census", "180 None, 49 exact 0.0, 13 -inf of 330", "S1", "open",
     "explain each class; part of L08"),
    ("L56", "B2", "stray tracked root files", "stats_comparison.json; audit_after_patch.txt", "not under audit/", "S1", "open", "move or remove before merge"),
    ("L57", "B2", "unseeded np.random in formula generators", "physics_aware_regressor.py (35 sites)",
     "np.random.uniform with no local seed", "S1", "open", "confirm global seed set before calls (test_engine_seed_audit.py) or use a seeded rng"),
    ("L58", "B2", "7d45ebc and 81662dd share a message but not a patch", "git", "patch-ids differ", "S1", "open", "git show --stat both; document why"),
    ("L59", "B2", "tie rows to the scorer", "r2_canonical.py", "archive scripts stamp evaluator_sha256; no live gate", "S1", "open",
     "gate checks row evaluator_sha256 == sha256(r2_canonical.py)"),
]

if not P.exists():
    sys.exit("audit/LEDGER.csv not found")
rows = list(csv.reader(P.open()))
have = {r[0] for r in rows if r}
new = [r for r in ROWS if r[0] not in have]
upd = [r for r in ROWS if r[0] in have]
print(f"{len(new)} new rows, {len(upd)} ids already present (left untouched: {[r[0] for r in upd]})")
for r in new:
    print("  +", r[0], r[2])
if "--write" in sys.argv:
    with P.open("a", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for r in new:
            w.writerow(r)
    print("written. review with: git diff audit/LEDGER.csv")
else:
    print("dry run; use --write to append")
