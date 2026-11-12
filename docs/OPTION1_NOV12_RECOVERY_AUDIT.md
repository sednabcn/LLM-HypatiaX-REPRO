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

## 8. Four-arm evaluator implementation — source committed, not executed (12 November)

The first implementation pass is now committed on `promotion/rerun-code-review`:

- `hypatiax/experiments/benchmarks/exp1_four_way_matched.py` — new primary four-arm driver.
- `hypatiax/experiments/benchmarks/exp1_ablation.py` — Hybrid and PySR arms now additionally score their fitted predictors on the generated untouched outer test partition and record test R²/RMSE/MAE. Existing training and extrapolation fields are retained.
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py` — NN accepts a per-equation random seed from metadata; its test prediction uses the returned trained predictor, not its in-sample headline metric.
- `run_all.sh` — new `exp1_four_way_matched` stage; the legacy `exp1_five` stage remains manually selectable.
- `ci_runner/run_fresh_experiments.sh` — fresh campaign selects `exp1_four_way_matched` instead of legacy `exp1_five`.
- `config/fresh_rerun.yaml` — registers the four arms, shared outer test protocol, common predictive metrics and extrapolation regimes.

### 8.1 Evaluation design now encoded

Each Core-15 equation/seed uses the same deterministic `generate_data()` output for all four arms: one 80/20 split of the same 200 noisy samples. The training partition alone is supplied to fitting/prompting/model selection. The held-back 20% partition is scored after fitting using R², RMSE and MAE. The same generated near/medium/far extrapolation arrays are scored for all arms. The checkpoint records SHA-256 fingerprints for training, outer-test and extrapolation arrays.

Arm definitions:

1. `hybrid_llm_pysr`: existing Core-15 `run_condition('hypatia')` path, with strict live-LLM mode enforced.
2. `llm_only`: `PureLLMBaselineMethod` generated formula, evaluated on outer-test and extrapolation inputs with the repository's restricted formula evaluator; no PySR refinement.
3. `pysr_only`: existing raw PySR-only `run_condition`, scored on the same outer-test and extrapolation arrays.
4. `nn_only`: `ImprovedNNMethod` trained on the shared training partition with log preprocessing retained and OLS/secondary-NN fallbacks disabled; its returned neural predictor is scored on the untouched outer test and shared extrapolation arrays.

A common nominal timeout is configured for each arm's main generation/training stage. It is not a strict end-to-end per-arm compute budget: symbolic test/extrapolation scoring occurs after the timeout context, and the PySR wrapper's own timeout_in_seconds is distinct from the outer SIGALRM cap. The PySR population/iteration settings come from the frozen fresh-rerun environment. The driver fails closed if no Anthropic API key is present and enforces `HYPATIAX_STRICT=1` before loading the experiment modules. The summary also reports paired Hybrid-minus-baseline differences, wins/losses and per-equation deltas; the equation is the comparison unit, not the 200 generated rows. These are descriptive summaries, not a confirmatory significance claim.

### 8.2 Integration and limitations

The fresh campaign stage list now invokes the matched four-way driver and no longer invokes `exp1_five` as the primary comparison. The legacy five-system script and stage remain available for explicitly exploratory/manual use, but its scores must not be substituted for the matched table.

Important: this is a source implementation pass, not a validated experiment. No Python import check, unit test, static checker, dry run, benchmark, API call, or workflow was run. Before scientific execution, code review must still verify that all 15 equations produce valid predictors for all four arms, that the restricted LLM formula evaluator accepts the actual generated formula forms, and that timeouts/partial failures are recorded as missing rather than silently scored. A failed arm remains an explicit failure and must not be replaced with a fallback score.

### 8.3 Routing and ablation disclosure

- `degradation_tau` remains null. The manifest records ensemble fallback/no calibrated selective-routing claim. Do not tune tau on the outer test set.
- The Core-15 gate coverage remains three implemented gates only (`llm_acceptance`, `complexity_routing`, `pysr_prior`). Three unavailable gates are not interpreted as no-effect.
- The new four-way driver does not claim a complete six-gate ablation.

**Status after implementation:** matched evaluator and fresh-run stage are wired in source; scientific validity and operational readiness remain unverified until the user authorizes and executes the run.
### 8.4 Gate-ablation execution prerequisite

Further inspection of `scripts/phase3_all.py` shows that the three wired leave-one-gate-out arms are not independently runnable as a clean fresh study: Phase 3 requires a fresh Phase 2 closure manifest and fresh Pure-LLM rows, followed by its own preflight and close procedure. Phase 2 is explicitly deferred in `config/fresh_rerun.yaml` because its candidate-count, timeout, and evaluator/prompt-provenance decisions are unresolved. Historical `p2/` or `phase2_out/` artifacts are expressly forbidden as substitutes. Therefore the Nov 15 fresh campaign does **not** claim or execute a three-gate leave-one-out ablation. The three implemented switches are documented as available; the three absent switches remain unavailable. Completing even the three-gate study requires a separate Phase 2 protocol decision and fresh closure before Phase 3 can proceed.

### 8.5 NN arm purity correction

Inspection of `ImprovedNNMethod` revealed that its legacy wrapper can replace a weak NN with log-space OLS or a second linear-space NN. Those fallback paths would make the fourth arm a composite fallback system rather than NN-only. The matched driver now passes `disable_fallback=True`; the wrapper honors this flag and the result provenance records `fallbacks_disabled=True`. Log preprocessing and the primary neural architecture remain enabled. If the primary NN fails, the arm is recorded as failed rather than substituted with OLS or another model.

### 8.6 NN training-row parity correction

A final adapter review found that ImprovedNNMethod internally split the already-shared 160-row training partition a second time. With fallbacks disabled, that internal validation subset was not needed for model selection, so the NN was fitting on only 128 rows while the symbolic arms received all 160. The matched NN-only call now sets `use_all_training_data=True`: the primary NN fits on every row in the common 160-row training partition. The internal diagnostic aliases are explicitly not treated as a held-out validation set, and the wrapper records `r2_heldout/rmse_heldout=null` with `heldout_scope=not_applicable_all_supplied_training_rows_used`. The outer 40-row test partition remains outside the NN call and is scored only by the matched driver after fitting.

This corrects the avoidable training-row imbalance; it does not make compute, hyperparameter search, or inductive bias identical across methods. Those method-specific differences and actual runtimes still need to be disclosed. This correction is source-only and has not been executed or validated.

### 8.7 LLM-only information-regime correction and evaluator regex fix

Static trace into PureLLMBaseline.generate_formula() confirms that its X and y arguments are accepted only for call compatibility: the implementation explicitly says they are not used, and the standard prompt contains the equation/task description, domain, variable names, and optional protocol constants, but no training examples or fitted statistics. The matched driver had been passing X_train/y_train and describing the arm simply as LLM-only, which could imply a data-conditioned baseline. The driver and manifest now identify this arm explicitly as a **zero-shot, task-description-conditioned LLM baseline**; its diagnostics record `training_arrays_used_by_model=false`. The arrays are passed through the wrapper interface but do not inform generation. The Hybrid, PySR and NN arms remain data-conditioned. Comparisons must disclose this information-regime asymmetry and must not claim equal effective information access. The zero-shot arm is useful as a prior-knowledge baseline, but it is not an apples-to-apples learner comparison.

The same trace found that two raw-string regexes in the shared restricted formula evaluator had doubled backslashes (`\\\\s` etc.), causing them to match literal backslash sequences rather than whitespace. This broke optional bracket-prefix stripping and assignment-formula extraction. Both patterns have been corrected to normal whitespace regexes. The primary PureLLM prompt asks for a `def formula(...)` function, which takes the direct restricted-AST path; the correction also repairs the evaluator's supported assignment/expression input forms. Neither change has been executed or tested in a runtime.

### 8.8 Hybrid participation and timeout-scope audit

A static trace of HybridDiscoverySystem._discover_with_retry() showed that an LLM proposal can fail or be skipped while the symbolic retry loop continues with pure PySR. The previous matched driver verified only that llm_enabled=True, which proves configuration intent but not actual LLM participation. The driver now fails the Hybrid arm as missing if the returned provenance does not report llm_called=True. A later pure-PySR retry may still win and remain a valid Hybrid-system outcome when an earlier LLM proposal was actually made; the engine preserves that attempt-level provenance.

The timeout implementation also needs precise interpretation. _Timeout is a Unix SIGALRM context. In the symbolic adapter it wraps HybridDiscoverySystem.discover() or PySRRegressor.fit(), but outer-test and extrapolation prediction/scoring happen after that context. The LLM and NN wrappers similarly time their generation/training call, with prediction scoring after it. Therefore the configured common value is a main-stage timeout, not a strict end-to-end arm wall-clock limit. Actual full-arm elapsed time is recorded by the outer four-way wrapper. PySR's internal timeout_in_seconds is separately configured and may exceed the outer alarm; process interruption/cleanup behavior has not been runtime-verified. Do not describe these settings as equal total compute budgets or claim that SIGALRM reliably terminates a Julia subprocess.

This pass also confirms by static inspection that Hybrid and raw PySR receive the same X_train, y_train arrays through dataset_override; Hybrid's discover(X_train, y_train, ...) and PySR's model.fit(X_train, y_train, ...) do not receive the outer test arrays. The shared data hashes and common test scoring remain the intended comparison basis. This is source review only: no Python execution, Julia/PySR run, LLM call, or experiment has been performed.
