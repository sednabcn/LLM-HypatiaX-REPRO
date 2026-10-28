import json, math, re, sys
import numpy as np

V = "hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py"
F = "hypatiax/data/results/comparison_results/noise-noiseless/15/hypatiax_defi_benchmark_v3c2_results.json"
m = re.search(r"^\s*CLIP_LO\s*=\s*(-?[0-9.eE+-]+)", open(V).read(), re.M)
CLIP_LO = float(m.group(1)) if m else float(sys.argv[1])
NAME = "Optimal LP Position (Kelly)"
cases = json.load(open(F))["cases"]

def stats(vals, denom):
    arr = np.array(vals, dtype=float)
    clipped = np.clip(arr, CLIP_LO, 1.0)
    return (len(arr), round(float(np.median(clipped)), 4) if len(arr) else None,
            round(float(np.mean(clipped)), 4) if len(arr) else None,
            round(100 * int(np.sum(arr > 0.9)) / denom, 2), round(100 * int(np.sum(arr > 0.99)) / denom, 2))

def collect(method, drop47=False, nan47=False, standard_only=True):
    out, n_cases = [], 0
    for c in cases:
        if standard_only and c.get("extrapolation_intractable"):
            continue
        if drop47 and c["test_case"] == NAME:
            continue
        n_cases += 1
        v = c["results"].get(method, {}).get("test_r2")
        if nan47 and c["test_case"] == NAME and method != "pure_llm":
            v = float("nan")
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            out.append(float(v))
    return out, n_cases

print("CLIP_LO =", CLIP_LO, "| standard cases:", sum(not c.get("extrapolation_intractable") for c in cases), "of", len(cases))
print("columns: n, median, mean_clip, pct>0.9, pct>0.99")
for method in ("pure_llm", "neural_network", "hybrid"):
    for label, kw in (("as published", {}), ("guard patched (47 = NaN)", {"nan47": True}),
                      ("47 flagged intractable", {"drop47": True})):
        v, d = collect(method, **kw)
        print(f"{method:15} {label:26}", stats(v, max(d, 1)))
