import json, glob, math, statistics as st, numpy as np
from collections import Counter
SRC = "hypatiax/data/results/ablation/exp1_ablation/exp1_ablation_results.json"
d = json.load(open(SRC))
rows = list(d.values()) if isinstance(d, dict) else d
print("equations in source:", len(rows), "| conditions in first:", [k for k, v in rows[0].items() if isinstance(v, dict) and "condition" in v])
FLOOR = -100.0
def fl(x):
    return FLOOR if x is None or not math.isfinite(x) else max(x, FLOOR)
H = {r["name"]: r["hypatia"] for r in rows if isinstance(r.get("hypatia"), dict)}
P = {}
for f in sorted(glob.glob("p2/pure_llm_seed*.jsonl")):
    for l in open(f):
        if l.strip():
            r = json.loads(l); P.setdefault(r["equation"], []).append(r["extrap_r2_far"])
print(f"{'equation':32} {'HDS far':>12} {'P far (med of seeds)':>22}")
hv, pv = [], []
for e in sorted(set(H) & set(P)):
    h = fl(H[e].get("extrap_r2_far")); p = fl(st.median(P[e]))
    hv.append(h); pv.append(p); print(f"{e:32} {h:12.4g} {p:22.4g}")
print("median far R2 (floored at -100)  HDS:", st.median(hv), " P:", st.median(pv))
print("HDS llm_called:", Counter(H[e].get("llm_called") for e in H), "| HDS sr_time_s max:", max(H[e].get("sr_time_s", 0) for e in H))
# split check: do HDS and P see the same far data?
import sys; sys.path.insert(0, "scripts")
from hypatiax.experiments.benchmarks import exp1_ablation as E
import p2_data
eq = {e["name"]: e for e in E.CORE_15}["Arrhenius"]
print("P far y[:3] seed 42:", p2_data.generate_case("Arrhenius", 42)["y_far"][:3])
for s in (0, 42, 99, 123):
    _, ye = E.generate_extrap_data(eq, regime="far", N=100, seed=s + E.EQ_ID.get("Arrhenius", 0) * 7)
    print(" seed", s, "far y[:3]:", ye[:3])
