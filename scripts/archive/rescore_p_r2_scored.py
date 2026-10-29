import glob, json, sys
sys.path[:0] = ["scripts", "."]
import run_pure_llm_arm as R, p2_data
from hypatiax.core.r2_canonical import r2_scored
out = []
for f in sorted(glob.glob("p2/pure_llm_*.jsonl")):
    for ln in open(f):
        r = json.loads(ln)
        c = p2_data.generate_case(r["equation"], r["seed"])
        sc = []
        for code in r["candidate_formulas"]:
            try:
                tr = r2_scored(c["y_train"], R.evaluate_formula(code, c["variable_names"], c["X_train"], c["constants"]))
                fa = r2_scored(c["y_far"], R.evaluate_formula(code, c["variable_names"], c["X_far"], c["constants"]))
            except Exception as e:
                tr = fa = (float("-inf"), f"error:{type(e).__name__}")
            sc.append((tr, fa))
        fin = [(s[0][0], i) for i, s in enumerate(sc) if s[0][0] > float("-inf")]
        pick = min(fin, key=lambda t: (-t[0], t[1]))[1] if fin else None
        out.append({"equation": r["equation"], "seed": r["seed"],
                    "stored_far": r["extrap_r2_far"],
                    "scored_far": sc[pick][1] if pick is not None else (float("-inf"), "failed"),
                    "picked": pick})
json.dump(out, open("phase2_finish_out/p_rescored_r2_scored.json", "w"), indent=1)
for o in out:
    if o["scored_far"][0] != o["stored_far"]:
        print(o["equation"], o["seed"], o["stored_far"], "->", o["scored_far"])
