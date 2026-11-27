# Proposal report: evaluating behaviour across training sample sizes

**Status:** design proposal only; no benchmark execution  
**Time budget:** 5 h 50 min maximum wall-clock per orchestration run

## Executive recommendation

After the fresh five-seed Core-15 replication, run a staged sample-size scaling study using a coordinator and restartable, checkpointing workers. The scientific design should vary training observations while holding equation families, seeds, arms, evaluation data, and algorithmic budgets fixed wherever possible.

A complete first design covers 15 equations, 10 seeds, four training sizes (32, 64, 128, 256), and three arms: 1,800 arm-runs. This is a multi-invocation target, not a single-job promise. A balanced 5-seed core is 900 arm-runs and should be the first coverage milestone if pilot timing indicates it is feasible.

## What this study can establish

It can show whether more training observations:
- reduce catastrophic far-OOD failures;
- improve or worsen candidate structural validity;
- change ordinary test performance and expression complexity;
- alter the relative behaviour of PySR-only, HypatiaX, and noLLM;
- produce diminishing returns or equation-specific scaling curves;
- increase wall-clock and resource cost.

It cannot, by itself, prove that a candidate expression is mathematically correct. The merged candidate gates are finite-sample structural screens; they are not formal symbolic proofs.

## Why the worker design changes

A seed-centric worker that owns a complete multi-equation run is a poor fit for a strict 350-minute deadline: slow shards can hold up the whole run, retries waste completed work, and a late timeout can lose uncheckpointed results.

The proposed architecture instead makes each equation × seed × sample-size × arm a restartable task. A coordinator assigns bounded leases, workers checkpoint every completed task, and a ledger makes retries and missing coverage explicit. The coordinator stops new work at T+305 min, finalises between T+325 and T+340, and retains a 10-minute safety margin.

Start with six workers; only scale to eight after measuring throughput and checking provider/API quotas, memory, and CPU contention. Workers must isolate output directories and must not publish duplicate authoritative results after lease expiry.

## Proposed stages

1. **After the five-seed replication:** verify the new gates' effect against the historical failure modes.
2. **Protocol and infrastructure:** implement coordinator, leases, task ledger, checkpointing, deterministic task IDs, and no-op integration tests.
3. **Calibration pilot:** sample equations/arms/sizes, estimate p50/p90 runtimes, and validate the 350-minute scheduler.
4. **Balanced core:** 15 equations × 5 historical seeds × 4 sizes × 3 arms = 900 arm-runs, split over resumable invocations if required.
5. **Extension:** add five pre-registered seeds for a total of 1,800 arm-runs.
6. **Analysis:** paired, equation-clustered scaling curves with explicit failure and missingness reporting.

## Critical design choices

- Use nested training subsets where possible: 32 ⊂ 64 ⊂ 128 ⊂ 256.
- Hold validation, in-distribution test, and far-OOD evaluation rows fixed across sample sizes for each equation/seed if the data-generation protocol allows it.
- Pair all three arms on the same equation/seed/size block.
- Keep per-arm search budgets fixed across sample sizes and disclose any differences between arms.
- Treat the 15 equation families as the primary scientific units; seeds are repeated stochastic replicates.
- Prioritise balanced paired blocks rather than allowing faster arms to dominate completed counts.
- Report raw far-OOD status and catastrophic counts, not only finite-score averages.

## Decision requested later

This is a proposal for review and future implementation. It does not authorise a benchmark run, model training, or expensive search. Before execution, approve the protocol, verify data-size feasibility, implement/test the worker scheduler, run a calibration pilot, and freeze the task manifest.
