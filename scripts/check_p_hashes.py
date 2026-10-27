import glob, importlib, inspect, json, sys

sys.path[:0] = ["scripts", "."]
import p2_data
import run_pure_llm_arm as R

mod = importlib.import_module("hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery")
cls = next(c for _, c in inspect.getmembers(mod, inspect.isclass)
           if c.__module__ == mod.__name__ and hasattr(c, "_generate_standard_prompt"))
obj = object.__new__(cls)  # _generate_standard_prompt does not use self

ok = bad = 0
for f in sorted(glob.glob("p2/pure_llm_*.jsonl")):
    for ln in open(f):
        if not ln.strip():
            continue
        r = json.loads(ln)
        c = p2_data.generate_case(r["equation"], r["seed"])
        prompt = obj._generate_standard_prompt(
            c["description"], c["domain"], c["variable_names"], {"constants": c["constants"]})
        entry = {"kwargs": {"messages": [{"role": "user", "content": prompt}]}}
        h = R.prompt_digest(entry)
        if h == r.get("prompt_sha256"):
            ok += 1
        else:
            bad += 1
            if bad <= 3:
                print("MISMATCH", r["equation"], r["seed"], "row:", str(r.get("prompt_sha256"))[:16], "rendered:", h[:16])

print("prompt hash match:", ok, "mismatch:", bad)
