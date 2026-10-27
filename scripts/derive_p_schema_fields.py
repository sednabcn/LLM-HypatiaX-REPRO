import collections, glob, json, os
import jsonschema

sch = json.load(open("phase2_row_schema.json"))
val = jsonschema.Draft202012Validator(sch)
os.makedirs("p2_schema", exist_ok=True)
EVAL = "r2_canonical@8f11733"
errs, temps, nulls = collections.Counter(), collections.Counter(), collections.Counter()
n = bad_expr = 0
for f in sorted(glob.glob("p2/pure_llm_*.jsonl")):
    rows = []
    for ln in open(f):
        if not ln.strip():
            continue
        r = json.loads(ln)
        gc = str(r.get("git_commit", ""))
        erp = r.get("effective_request_params") or {}
        reqs = erp.get("api_requests_per_call")
        sel, cands = r.get("selected_index"), r.get("candidate_formulas") or []
        has = sel is not None and sel < len(cands)
        if has and r.get("best_expression") != cands[sel]:
            bad_expr += 1
        d = dict(r)
        d.update({
            "r2_field": "extrap_r2_far",
            "status": "ok" if has else "no_formula",
            "formula": cands[sel] if has else None,
            "bypass_used": False,
            "model_id": r.get("model_id_returned"),
            "code_version": gc.replace("+dirty", ""),
            "code_dirty": gc.endswith("+dirty"),
            "config_hash": r.get("config_sha256"),
            "evaluator_version": EVAL,
            "temperature": (erp.get("params") or {}).get("temperature"),
            "n_llm_calls": sum(reqs) if reqs else r.get("n_calls"),
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "ablated_component": None,
            "config_diff": [],
        })
        if not has:
            d["r2_status"] = "not_scored"
        temps[d["temperature"]] += 1
        nulls["tokens_null"] += d["input_tokens"] is None
        for e in val.iter_errors(d):
            errs[e.message[:110]] += 1
        rows.append(d)
        n += 1
    with open(os.path.join("p2_schema", os.path.basename(f)), "w") as fh:
        for d in rows:
            fh.write(json.dumps(d) + "\n")
print("rows:", n, "| schema errors:", dict(errs) or 0)
print("temperature values:", dict(temps), "| rows with null tokens:", nulls["tokens_null"])
print("best_expression != formula[selected_index]:", bad_expr)
print("n_llm_calls sum:", sum(json.loads(l)["n_llm_calls"] for f in glob.glob("p2_schema/*.jsonl") for l in open(f) if l.strip()))
hds = {json.loads(l).get("evaluator_version") for f in glob.glob("p2/hds_*.jsonl") for l in open(f) if l.strip()}
print("HDS evaluator_version values:", hds)
