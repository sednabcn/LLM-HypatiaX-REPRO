#!/usr/bin/env python3
"""
paired_checker_audit.py
=======================
Measures how much of the "pure-LLM returned NaN" count is a CHECKER artifact.

Background
----------
* PureLLMBaseline.test_formula_accuracy() executes generated code in a namespace
  that has NO protocol constants (only numpy/math names).
* The hybrid arm's _eval_formula_r2() injects metadata["constants"].
* The benchmark JSON does not store the generated formula or the error text, so
  the 11 NaN cases cannot be diagnosed from existing results.

What this script does
---------------------
For every task it makes ONE pure-LLM generate_formula() call, then scores that
SAME formula three ways on the SAME train/test split:

  A   PureLLMBaseline.test_formula_accuracy       (what the paper's pure-LLM arm uses)
  B0  benchmark _eval_formula_r2, constants=None  (hybrid evaluator, no constants)
  B1  benchmark _eval_formula_r2, constants=meta  (hybrid evaluator, as hybrid uses it)

Reading the result
  A fails, B1 ok, B0 fails  -> missing constants are the cause (checker artifact)
  A fails, B0 ok            -> some other evaluator difference (namespace / arg handling)
  A fails, B1 fails         -> the formula itself is bad (genuine model failure)
Per-task A error text is saved, so NameError on a protocol constant is visible.

Limits (read before citing numbers)
  * Needs the API key and the hypatiax repo; costs one LLM call per task (~74).
  * Formulas are re-sampled, so this measures the RATE of checker artifacts,
    not the identity of the original 11 NaN tasks.
  * It does not touch the hybrid arm's own (separate) LLM call.

Usage (from the repo root, with ANTHROPIC key in the environment / .env):
  python paired_checker_audit.py --bench-dir /path/to/dir/with/v3c.py \
      --out audit_out [--limit 10] [--cases "Portfolio" "Impermanent"]
  python paired_checker_audit.py --inspect results.json     # no API; checks stored code
"""
import argparse, csv, importlib, json, math, re, sys, time
from pathlib import Path


def classify(a_ok, a_err, b0_ok, b1_ok, constants):
    """Return a short verdict label for one task."""
    names = set((constants or {}).keys())
    err = a_err or ""
    m = re.search(r"name '([^']+)' is not defined", err)
    missing = m.group(1) if m else None
    if a_ok:
        return "a_ok"
    if b1_ok and not b0_ok:
        return "constants_artifact" + (f" ({missing})" if missing in names else "")
    if b0_ok:
        return "other_evaluator_difference"
    return "formula_fails_everywhere"


def r2_ok(r2, ok):
    return bool(ok) and r2 is not None and not (isinstance(r2, float) and math.isnan(r2))


def inspect_json(path):
    data = json.loads(Path(path).read_text())
    recs = data["cases"] if isinstance(data, dict) and "cases" in data else data
    keys = ("llm_code", "python_code", "formula", "code")
    n = len(recs)
    found = {k: 0 for k in keys}
    err = 0
    for r in recs:
        blob = json.dumps(r)
        for k in keys:
            if f'"{k}"' in blob:
                found[k] += 1
        if '"error"' in blob:
            err += 1
    print(f"{path}: {n} records")
    print("records containing stored-code keys:", found)
    print("records containing an error field  :", err)
    if not any(found.values()):
        print("-> No generated formulas are stored; replay from this JSON is impossible. "
              "Run the paired audit instead.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench-dir", default=".", help="dir containing hypatiax_defi_benchmark_v3c.py")
    ap.add_argument("--repo", default=".", help="repo root (for the hypatiax package)")
    ap.add_argument("--out", default="audit_out")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--cases", nargs="+", default=None, help="name substrings")
    ap.add_argument("--inspect", metavar="JSON")
    args = ap.parse_args()

    if args.inspect:
        inspect_json(args.inspect)
        return

    sys.path[:0] = [str(Path(args.repo).resolve()), str(Path(args.bench_dir).resolve())]
    bench = importlib.import_module("hypatiax_defi_benchmark_v3c")
    from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import PureLLMBaseline

    protocol = bench.DeFiExperimentProtocol()
    cases = bench._apply_task_ids_defi(bench._get_test_cases())
    if args.cases:
        f = [s.lower() for s in args.cases]
        cases = [c for c in cases if any(s in c["name"].lower() for s in f)]
    if args.limit:
        cases = cases[: args.limit]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    llm = PureLLMBaseline()
    rows, code_dump = [], {}

    for i, tc in enumerate(cases, 1):
        print(f"[{i:02d}/{len(cases)}] {tc['name']}")
        row = {"task": tc["name"], "difficulty": tc.get("difficulty")}
        try:
            pcs = protocol.load_test_data(tc["domain"], num_samples=tc["num_samples"])
            match = next(((d, X, y, v, m) for d, X, y, v, m in pcs
                          if tc["name"].lower() in d.lower()), None)
            if not match:
                row["verdict"] = "no_protocol_match"; rows.append(row); continue
            desc, X_full, y_full, var_names, meta = match
            X_tr, y_tr, X_te, y_te = bench._aggressive_split(X_full, y_full, tc["config"])
            constants = meta.get("constants") or {}
            row["constants"] = ",".join(constants.keys())

            res = llm.generate_formula(desc, tc["domain"], var_names, meta)
            code = res.get("python_code") or ""
            code_dump[tc["name"]] = code

            a = llm.test_formula_accuracy(res, X_te, y_te, var_names, verbose=False)
            a_ok = bool(a.get("success"))
            row.update(A_ok=a_ok, A_r2=a.get("r2"), A_error=(a.get("error") or "")[:200])

            b0_r2, b0_ok = bench._eval_formula_r2(code, X_te, y_te, constants=None)
            b1_r2, b1_ok = bench._eval_formula_r2(code, X_te, y_te, constants=constants)
            b0_ok, b1_ok = r2_ok(b0_r2, b0_ok), r2_ok(b1_r2, b1_ok)
            row.update(B0_ok=b0_ok, B0_r2=b0_r2, B1_ok=b1_ok, B1_r2=b1_r2,
                       verdict=classify(a_ok, a.get("error"), b0_ok, b1_ok, constants))
        except Exception as e:  # keep going; record the failure
            row["verdict"] = f"script_error: {e}"[:160]
        rows.append(row)
        (out / "generated_formulas.json").write_text(json.dumps(code_dump, indent=2))
        time.sleep(0.2)

    fields = ["task", "difficulty", "constants", "A_ok", "A_r2", "A_error",
              "B0_ok", "B0_r2", "B1_ok", "B1_r2", "verdict"]
    with open(out / "paired_audit.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

    n = len(rows)
    a_fail = [r for r in rows if r.get("A_ok") is False]
    art = [r for r in rows if str(r.get("verdict", "")).startswith("constants_artifact")]
    oth = [r for r in rows if r.get("verdict") == "other_evaluator_difference"]
    gen = [r for r in rows if r.get("verdict") == "formula_fails_everywhere"]

    def hi(r, k):
        v = r.get(k)
        return isinstance(v, float) and not math.isnan(v) and v > 0.99
    a_hi = sum(hi(r, "A_r2") for r in rows)
    b1_hi = sum(hi(r, "B1_r2") for r in rows)

    print("\n" + "=" * 60)
    print(f"tasks scored                       : {n}")
    print(f"pure-LLM checker failures (A)      : {len(a_fail)}")
    print(f"  ...explained by missing constants: {len(art)}")
    print(f"  ...other evaluator difference    : {len(oth)}")
    print(f"  ...formula fails under any check : {len(gen)}")
    print(f"R2>0.99 under A (as in paper)      : {a_hi}/{n}")
    print(f"R2>0.99 under B1 (constants given) : {b1_hi}/{n}")
    print(f"details: {out/'paired_audit.csv'}  formulas: {out/'generated_formulas.json'}")


if __name__ == "__main__":
    main()
