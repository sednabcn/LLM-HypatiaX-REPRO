# Step 5 scan

## A. NN headline metric on the full data (in-sample)

Lines where `_safe_r2(y, ...)` / `_safe_rmse(y, ...)` score against the array the method was handed
(in files that define ImprovedNN). If `y` includes training rows this is in-sample; compare with the held-out `y_test`/far metric.

- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py`: lines 1607, 1608, 1954, 1955, 2161, 2162, 2195, 2196, 2233, 2234, 2569, 2570, 2632, 2637, 2656, 2657, 2683, 2684
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py`: lines 1658, 1659, 2029, 2030, 2239, 2240, 2273, 2274, 2318, 2319, 2641, 2642, 2737, 2742, 2761, 2762, 2788, 2789

**Decision (yours):** report held-out only, or add an `r2_heldout` field next to the existing one.

## B. get_llm_prior() call sites

| file | line | cache_salt passed | blind passed |
|---|---|---|---|
| `hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py` | 1655 | **NO** | no |

Without `cache_salt=f"seed{seed}"` every seed replays one cached completion (no LLM variance across seeds).
