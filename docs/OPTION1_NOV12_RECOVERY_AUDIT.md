# Option 1 / Core-15 rerun recovery audit — 12 November 2026

**Purpose:** stop Core-295 dataset expansion and prepare the original Core-15 rerun path for the user's 15 November start.

**Scope:** source inspection only. No experiment, test, validator, workflow, paid compute, or live API call was run. This document does not authorize execution.

## 1. Option 1 interpretation

For this recovery, Option 1 means returning to the manuscript's original Core-15 equation population and the existing experiment scripts. Core-295 candidate discovery, catalogue construction, source retrieval, task planning, and shard execution are out of scope for the 15 November rerun.

The existing fresh-run launcher does not invoke Core-295 stages. Its campaign includes Core-15 stages such as `exp1_ablation` and `exp1_five`, alongside the wider DeFi, Feynman, Nguyen-12, noise, routing, and supplementary stages.

## 2. Repository / branch finding

- Working branch inspected: `promotion/rerun-code-review`.
- Comparison branch: `rerun/integration`.
- The promotion branch is 1,278 commits ahead of `rerun/integration` (no commits behind) and contains the Core-295 catalogue, source audits, planner, adapters and execution tooling, as well as additional rerun changes.
- `rerun/integration` itself is not a drop-in rollback target: it has an older fresh-run wrapper/configuration and its `config/fresh_rerun.yaml` contains historical expected-result fields that the current promotion-branch fresh protocol intentionally omits.

**Decision for this audit:** do not reset, rebase, merge, or switch branches as part of the Option 1 recovery. Preserve the current branch and explicitly keep Core-295 outside the run plan. A branch change requires a separate deliberate decision.

## 3. Current Option 1 execution path

Files inspected on `promotion/rerun-code-review`:

- `config/fresh_rerun.yaml` — fresh input protocol; no historical expected-result values.
- `ci_runner/run_fresh_experiments.sh` — isolated fresh-run wrapper.
- `run_all.sh` — stage dispatcher and protocol environment loader.
- `.github/workflows/ci_fresh_rerun.yml` — manual workflow requiring explicit `RUN_FRESH_EXPERIMENTS` confirmation.
- `hypatiax/experiments/benchmarks/exp1_ablation.py` — Core-15 PySR-only / HypatiaX comparison, with optional no-LLM arm.
- `hypatiax/experiments/benchmarks/exp1_five_system.py` — five-method Core-15 comparison.

The wrapper requires a new empty absolute `RESULTS_DIR` outside the repository, a clean checkout, pinned Python dependencies, Julia 1.11/PySR, and `ANTHROPIC_API_KEY`. It performs a live API preflight and a synthetic PySR warm-up before benchmark stages. These are execution prerequisites, not actions performed during this audit.

## 4. Scientific blockers for the revised claim

The paper's new proposition is conditional: determine when Hybrid outperforms LLM, PySR and NN, and when it does not. The existing scripts are not yet sufficient evidence for a fair four-way superiority claim.

### 4.1 Core-15 ablation is not a four-way comparison

`exp1_ablation.py` compares `pysr_only` and `hypatia`, with an optional `hypatia_nollm` condition. It is useful for the Hybrid-versus-PySR/LLM-contribution question, but it does not by itself provide a matched LLM-only and NN-only comparison.

### 4.2 Five-system comparator semantics need explicit treatment

`exp1_five_system.py` uses five wrappers from `run_comparative_suite_benchmark_v2.py`. Its own module documentation states that the `Hybrid v50_2` wrapper calls a PySR subprocess without the LLM proposal step; it is not the same method/call path as the LLM-enabled `hypatia` condition in `exp1_ablation.py`.

The current five-system audit also identifies a metric comparability problem for the NN row: the headline score is computed on all supplied training rows, while its internal validation split is used for model/fallback selection. The internal validation score is therefore not an untouched final-test estimate. The outer generated test split is not passed to this wrapper. Do not present these scores as a fair held-out four-way comparison.

**Required before making the central claim:** define one matched evaluation table with the same equation, generated samples, train/test split, extrapolation sets, seeds, scoring function and comparable tuning budget for Hybrid, LLM-only, PySR-only and NN-only. If existing wrappers cannot satisfy this, report them as separate exploratory comparisons and do not claim matched superiority.

### 4.3 Routing threshold remains intentionally unset

`config/fresh_rerun.yaml` sets `routing_policy.degradation_tau: null`. The fresh runner removes any inherited `HYPATIAX_ROUTING_DELTA_TAU` when tau is null. The calibration manifest remains a draft with no calibration equations or candidate thresholds.

The implemented fail-closed behavior routes to the ensemble when tau is unavailable. This is not evidence that the manuscript's calibrated pure-LLM routing rule has been reproduced. Do not invent a threshold or calibrate it on Core-15 evaluation outcomes. Either complete a separate valid training-only calibration before the rerun, or freeze and disclose the unset-tau/ensemble-fallback condition as a protocol limitation before execution.

### 4.4 Core-15 leave-one-gate-out coverage is partial

The current fresh protocol records that only `llm_acceptance`, `complexity_routing`, and `pysr_prior` are wired for Core-15 HDS v50_2. The NN-specific degradation probe, NN augmentation and blend-weight gates are unavailable in this architecture. Do not report a complete six-gate Core-15 ablation or interpret missing gates as no effect.

## 5. Immediate recovery actions

1. Keep Core-295 discovery and execution out of the 15 November campaign.
2. Freeze the current Core-15 equation catalogue, protocol file, code commit, seeds, model settings, data-generation ranges and metrics before any run.
3. Decide the intended primary campaign scope: Core-15 first, then wider benchmark suites only where their protocols and comparator semantics are ready.
4. Resolve or explicitly freeze the unset-tau behavior before execution.
5. Audit/fix the matched four-method comparison and NN held-out evaluation before using it to support the paper's central proposition.
6. Prepare an isolated output directory and preserve all raw outputs, logs, manifests and failures.
7. Do not start the workflow or make live API calls until the user explicitly authorizes execution.

## 6. Status

- Core-295 expansion: stopped for this rerun.
- Option 1 / Core-15 code path: present and identified.
- Four-way fair comparison: **not yet certified**.
- Tau calibration: **not ready; tau remains null**.
- Core-15 six-gate ablation: **partial, not complete**.
- Workflow execution: **not run**.
- Scientific rerun: **not run**.

**Bottom line:** Option 1 is recoverable without discarding the entire current branch, but the manuscript's revised Hybrid-versus-LLM/PySR/NN claim requires a fair matched comparator design. The 15 November target should be a frozen, auditable rerun protocol—not an unsupported promise of Hybrid superiority.

## 7. Follow-up source trace — matched comparison correction (12 November)

A deeper read of the actual method adapters confirms the four-way problem and makes the required correction more specific.

### 7.1 The current five-system rows are the wrong four systems

`exp1_five_system.py` selects `PureLLMBaselineMethod`, `ImprovedNNMethod`, `HybridAllDomainsMethod`, `SymbolicEngineMethod`, and `HybridSystemV50_2Method`. This is a five-row exploratory suite, not the requested four-way comparison. In particular:

- `HybridSystemV50_2Method` delegates to the v50_2 PySR subprocess path; its module documentation explicitly says there is no LLM proposal step. It cannot stand in for the LLM+PySR Hybrid condition.
- `HybridAllDomainsMethod` is a separate LLM+NN residual hybrid architecture, not the Core-15 HDS v50_2 LLM+PySR method.
- `SymbolicEngineMethod` is a symbolic engine wrapper and must be checked for exact PySR-only semantics before it is labelled PySR-only.
- The Core-15 Hybrid condition already exists in `exp1_ablation.py` as `run_condition(..., condition='hypatia')`; it invokes `HybridDiscoverySystem.discover()` with `use_llm=True` in strict live-API mode. The same function has a `hypatia_nollm` condition, but that is not an LLM-only baseline.

### 7.2 The outer test split is generated and then discarded

`exp1_five_system.run_method_on_equation()` calls `generate_data()` and receives `X_train, X_test, y_train, y_test`. It passes only `X_train, y_train` to each method and does not use `X_test, y_test` for headline scoring. The returned `train_r2/train_rmse` fields are simply copied from `result.r2/result.rmse`, even though those fields do not have a consistent evaluation scope across wrappers.

For NN specifically, `ImprovedNNMethod.run()` makes an internal 80/20 split of the arrays passed to it, but its headline `r2/rmse` is computed on the full supplied `(X, y)` dataset (in-sample); a separate `r2_heldout/rmse_heldout` diagnostic is retained in metadata. Therefore the NN headline is not an untouched outer-test metric either.

### 7.3 Correct four-arm definition

The intended primary comparison should be:

1. **Hybrid:** Core-15 `HybridDiscoverySystem` via the existing LLM-enabled `hypatia` path (LLM proposal + PySR/refinement).
2. **LLM-only:** a clearly specified LLM proposal/prediction path with no PySR refinement. Verify that its predictions can be evaluated on the shared outer test set; do not silently substitute the separate all-domains hybrid.
3. **PySR-only:** raw PySR fit with no LLM proposal, using the same training rows and an explicit test predictor.
4. **NN-only:** NN trained on the same training rows, with model selection confined to training/validation data and final scoring on the shared untouched outer test rows.

All four arms must receive the same per-equation/per-seed training dataset. The test set must not be passed into fitting, early stopping, model selection, routing-threshold choice, or formula selection. Store test R², RMSE and MAE from predictions on the same `X_test`; report near/medium/far extrapolation separately on common generated arrays. Keep symbolic equation/parameter recovery metrics separate from predictive metrics because they are not defined equivalently for NN.

The LLM-only arm is a key unresolved implementation detail: `PureLLMBaselineMethod` exists, but its returned result/prediction contract must be verified before it can be scored on the shared test array. If no valid predictor can be extracted without adding an unvalidated method path, mark the four-way comparison **not ready** rather than fabricate an LLM-only result.

### 7.4 Nov 15 safety decision

Until the matched four-arm evaluator is implemented and reviewed, do not use `exp1_five` as evidence for the revised four-way claim. The current `exp1_five` stage may remain an explicitly exploratory legacy five-system output only if its labels and metric scopes are clearly disclosed; otherwise defer that stage from the Nov 15 campaign. Do not change the scientific method or dispatch workflows as part of this source audit.

### 7.5 Tau and gate decisions retained

- Keep `degradation_tau: null`; runner intentionally unsets the inherited tau environment variable. Record ensemble fallback and make no calibrated selective-routing claim.
- Report only the three implemented Core-15 gates (`llm_acceptance`, `complexity_routing`, `pysr_prior`). The three missing gates remain unavailable, not zero-effect.
