# Sample-size scaling study: scientific protocol

**Status:** proposed / not executed  
**Repository:** `sednabcn/LLM-HypatiaX-REPRO`  
**Study family:** follow-on to the Core-15 candidate-gate five-seed replication  
**Execution constraint:** hard wall-clock ceiling of 5 h 50 min (350 min) per orchestration run

## 1. Purpose and research questions

This study will measure how the behaviour of the three `exp1_ablation` arms changes as the number of training observations increases, after the Core-15 candidate gates are present in the merged codebase.

Primary questions:

1. Does increasing training sample size reduce catastrophic far-OOD failures?
2. Does it change structural-validity / candidate-rejection rates?
3. Does the effect differ between PySR-only, HypatiaX, and noLLM?
4. Are gains monotonic, saturating, or equation-dependent?
5. What is the compute cost per additional training observation and per successful result?

The scientific target is the *sample-size response curve*, not merely a larger aggregate score.

## 2. Design overview

Use a blocked, repeated-measures factorial design:

- **Equation families:** all 15 Core-15 equations.
- **Arms:** PySR-only, HypatiaX, noLLM, with identical benchmark semantics and arm-specific budgets recorded.
- **Training sample-size levels:** begin with 32, 64, 128, and 256 observations per equation. Add 512 only if the pilot shows the level is supported by the data generator and fits within the measured compute envelope. If the repository's canonical generator has a different valid range, use the nearest pre-registered geometric sequence and document the deviation before execution.
- **Seeds:** 10 planned seeds, including historical seeds 42, 99, 123, 777, and 2024 plus five newly fixed seeds. Freeze the complete seed list in the manifest before running.
- **Replicates:** each equation × seed × sample-size combination is a block; run all three arms on the same generated split / seed so comparisons are paired.
- **Data leakage:** generate train, validation, in-distribution test, and far-OOD test sets independently according to the existing benchmark protocol. Only training-set size changes across the primary comparison. Hold validation/test sizes and OOD construction fixed where the protocol permits.
- **Primary unit of scientific generalisation:** equation family (15 units); seeds and sample-size levels are repeated observations, not independent equation families.

The complete planned matrix is 15 × 10 × 4 × 3 = **1,800 arm-runs**. This is a target inventory, not a promise that all runs fit in one 5 h 50 min job. The time-bounded scheduler will complete deterministic shards and carry unfinished work into a later invocation.

## 3. Comparability and controls

1. Pin the repository commit, Python/runtime, dependency lock, LLM model/version, prompts, PySR engine, population/iteration budgets, retry policy, and environment variables.
2. Keep algorithmic budgets fixed across sample-size levels within each arm. Record the existing arm-specific budgets; do not silently equalise historically different budgets.
3. Reuse the same seed-specific generated data across arms at a given sample size. Where possible use nested training subsets (32 ⊂ 64 ⊂ 128 ⊂ 256) so sample-size differences are not confounded by unrelated draws. Randomise row order deterministically.
4. Keep validation/test/OOD rows fixed across sample-size levels for a seed/equation, unless the existing generator makes this impossible; document exact behavior.
5. Preserve candidate gates and log every candidate validation result, rejection reason, selected route, fallback, and selected expression.
6. Run no code-path changes between levels. If code changes, start a new protocol version and do not pool the results.
7. Capture failed, timed-out, skipped, and incomplete runs as explicit statuses. Never silently drop them.

## 4. Worker architecture for the 5 h 50 min clock limit

Use a **coordinator + leased shard-worker architecture**, not one long-lived worker per seed that must finish its whole matrix.

### Coordinator
- Creates a run ID and immutable manifest containing commit SHA, protocol version, seed list, sample sizes, equation IDs, arms, and expected task IDs.
- Expands the matrix into atomic tasks keyed by `equation_id/seed/sample_size/arm`.
- Assigns tasks to workers using bounded leases; records worker ID, attempt, start time, heartbeat, deadline, and terminal status.
- Enforces global deadline and stops dispatching before the hard limit.
- Collects only validated, schema-compliant result artifacts; deduplicates by task ID and attempt policy.
- Writes a completion manifest and coverage report, including missing task IDs.

### Workers
- Use stateless, restartable workers. A worker claims a bounded batch, runs tasks sequentially, and checkpoints each task immediately after completion.
- Recommended initial concurrency: **6 workers**, subject to API/provider quotas and observed CPU/memory. Increase to 8 only after a pilot demonstrates no throttling, memory pressure, or throughput regression.
- Avoid concurrent duplicate claims with atomic task leases / compare-and-set semantics.
- Heartbeat between tasks and during long tasks where supported. A worker that loses its lease must not publish a second authoritative result.
- Keep per-task logs and artifacts isolated by run ID, task ID, and attempt number.
- Workers must not share mutable PySR output directories, caches, or temporary filenames.

### Time budget (350 minutes total)
- 0–10 min: checkout, environment verification, manifest validation.
- 10–35 min: calibration/pilot tasks and runtime estimate.
- 35–305 min: main task dispatch, in bounded waves.
- 305–325 min: stop new claims; allow in-flight tasks only if they can finish safely.
- 325–340 min: collect, validate, and aggregate completed shards.
- 340–350 min: write final status/manifest and clean shutdown.

The coordinator's hard stop is **T+340 min**, leaving a 10-minute safety margin before the 5 h 50 min ceiling. If the hosting platform's actual timeout is shorter, set the stop time to at least 15 minutes before that platform limit.

### Adaptive scheduling and graceful degradation
- First pilot a balanced sample across equations, arms, and at least two sample-size levels. Estimate p50/p90 task runtime by arm and sample size.
- Use those estimates to calculate safe worker waves; never start a task unless its configured task timeout plus aggregation reserve fits before T+305.
- Prioritise balanced coverage: complete the same set of equation/seed/sample-size blocks across all three arms before spending remaining time on extra replicates. Do not let a fast arm create an apparently complete comparison while its paired arms are missing.
- If the full 1,800-task matrix cannot fit, preserve a pre-declared balanced core: all 15 equations × 5 historical seeds × 4 sizes × 3 arms (900 runs), then extend to the five new seeds in later invocations. Within any invocation, schedule paired triplets and complete blocks.
- Persist a resumable queue and checkpoint after every task. A later invocation resumes only missing tasks using the exact same manifest and commit. A deliberate fresh rerun must use a new run ID and explicit `resume=false`.
- Never use a partial run as if it were a complete factorial result. Report coverage by equation, seed, size, and arm.

## 5. Outcomes

### Primary outcomes
- Catastrophic far-OOD failure incidence, with the exact threshold/status definition inherited from the benchmark and frozen in the manifest.
- Equation-level catastrophic failure rate across seeds at each sample size and arm.
- Structural candidate-validation pass/reject/unknown rates and rejection reasons.
- Paired change in far-OOD performance as sample size increases.

### Secondary outcomes
- In-distribution test R² and original-unit MAE/RMSE.
- Raw far-OOD R² and original-unit errors (retain non-finite values and status labels).
- Expression complexity, variable coverage, and structural form.
- Route selection, fallback frequency, retry count, and runtime.
- Resource consumption where available (CPU time, peak memory, API calls/tokens/cost).

Do not report only medians over finite far-OOD values: include failure counts and raw status-aware distributions.

## 6. Statistical analysis

- Plot sample-size response curves separately by arm and equation; show uncertainty across seeds.
- Use paired within-block contrasts (same equation, seed, sample size) for arm comparisons.
- Estimate sample-size trends with equation-level clustering / hierarchical models or a cluster bootstrap over the 15 equation families. Do not treat 1,800 arm-runs as 1,800 independent scientific units.
- Report effect sizes and confidence intervals, not only p-values.
- Test arm × log2(sample size) interactions and report equation heterogeneity.
- Pre-specify the catastrophic-failure comparison as the primary endpoint. Treat multiple secondary metrics as exploratory or apply a stated multiplicity procedure.
- Compare the historical five-seed baseline descriptively only where code, data generation, and evaluation semantics are demonstrably compatible.

## 7. Validity threats and decision rules

- **Data-size feasibility:** verify that every equation has enough generated observations and that the chosen sizes are meaningful before freezing the manifest.
- **Changing test sets:** if evaluation rows change with training size, sample-size effects are confounded; avoid or explicitly model this.
- **Compute-budget confounding:** fixed per-fit budgets may create size-dependent timeouts; report them and avoid selective completion.
- **LLM stochasticity/provider drift:** pin model identifiers where possible and record provider metadata.
- **Gate interpretation:** candidate-gate pass is a structural screen, not a formal proof of correctness or extrapolation.
- **Missingness:** timeout and failed runs are outcomes, not ignorable missing data.

Interpretation:
- **Supportive:** catastrophic failures and structural-invalid selections decline with sample size, with stable or improved ordinary predictive performance.
- **Mixed:** in-distribution metrics improve but far-OOD failure remains or shifts to particular equations.
- **Null/negative:** no consistent trend, or larger samples increase runtime/failure without meaningful validity gains.

## 8. Required artifacts

Store one immutable run directory per execution, containing:

- `sample_size_study_manifest.json`
- `sample_size_study_task_ledger.jsonl`
- per-task result JSON and logs
- `sample_size_study_coverage.csv`
- `sample_size_study_summary.json`
- `sample_size_study_report.md`
- runtime/resource profile and worker diagnostics

The report must state planned, completed, failed, timed-out, skipped, and missing counts. Include the exact commit and configuration provenance.

## 9. Execution gates

Before any expensive run:
1. Review and approve this protocol.
2. Verify the merged Core-15 gate implementation and current benchmark entry point.
3. Implement and test the coordinator/worker queue on synthetic no-op tasks.
4. Run a small calibration pilot and measure p50/p90 task runtimes.
5. Recompute the feasible matrix under the 350-minute ceiling.
6. Freeze the manifest and only then launch the full study with explicit authorisation.

**No experiment is launched by this document or its commit.**
