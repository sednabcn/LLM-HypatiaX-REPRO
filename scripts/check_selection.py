import json, glob

o = {(x["equation"], x["seed"]): x["picked"]
     for x in json.load(open("phase2_finish_out/p_rescored_r2_scored.json"))}

diff = 0
for f in sorted(glob.glob("p2/pure_llm_*.jsonl")):
    for ln in open(f):
        if not ln.strip():
            continue
        r = json.loads(ln)
        k = (r["equation"], r["seed"])
        if r.get("selected_index") != o[k]:
            diff += 1
            print(k, "stored:", r.get("selected_index"), "rescored:", o[k])

print("rows where selection differs:", diff)
