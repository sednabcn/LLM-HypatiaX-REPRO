#!/usr/bin/env python3
"""Static checks for the open code findings. Run from the repo root.
Severity: FAIL (must fix or justify), WARN (review), INFO (disclose/record).
Exit 1 if any FAIL."""
import glob, re, sys, pathlib, collections

HY = "hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py"
V2 = "hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py"
AB = "hypatiax/experiments/benchmarks/exp1_ablation.py"
RA = "run_all.sh"


def lines(p):
    try:
        return pathlib.Path(p).read_text(errors="replace").splitlines()
    except FileNotFoundError:
        return None


results = []  # (sev, id, file, lineno, text)


def find(sev, cid, path, regex, must_not=None, msg=""):
    ls = lines(path)
    if ls is None:
        results.append(("WARN", cid, path, 0, "FILE MISSING"))
        return
    for i, l in enumerate(ls, 1):
        if re.search(regex, l) and not (must_not and re.search(must_not, l)):
            results.append((sev, cid, path, i, (msg + " | " if msg else "") + l.strip()[:110]))


def absent(sev, cid, path, regex, msg):
    ls = lines(path)
    if ls is None:
        results.append(("WARN", cid, path, 0, "FILE MISSING"))
    elif not any(re.search(regex, l) for l in ls):
        results.append((sev, cid, path, 0, msg))


# L-new: None / nan handling in hybrid decision logic
find("FAIL", "S01", HY, r"llm_ok\s*=.*np\.isfinite\(llm_r2\)", r"is not None",
     "llm_r2 may be None -> np.isfinite(None) TypeError")
find("FAIL", "S02", HY, r'"r2":\s*0\.0', None, "failure scored as 0.0")
absent("FAIL", "S03", HY, r"isnan\(nn_r2\)|isfinite\(nn_r2\)",
       "no explicit nan branch for nn_r2: nan NN falls through decision logic")
# Harness wrapper
find("FAIL", "S04", V2, r'eval_\.get\("r2",\s*0\.0\)', None, "missing r2 defaults to 0.0")
find("WARN", "S05", V2, r'for _key in \("evaluation", "nn_result", "llm_result", "result"\)', None,
     "_extract_eval fallthrough ignores decision")
find("WARN", "S06", V2, r'r2=float\("-inf"\),\s*rmse=float\("inf"\)', None,
     "_unavailable returns -inf/inf (JSON -Infinity); use None + reason")
find("INFO", "S07", V2, r'"force_llm":\s*True', None, "FIX 3 result-informed routing override: disclose")
find("WARN", "S08", AB, r'get\("rmse",\s*float\("inf"\)\)', None, "rmse default inf (audit-M3)")
# run_all.sh controls
absent("FAIL", "S09", RA, r"export HYPATIAX_R2_SIGN_FLIP", "SIGN_FLIP not exported explicitly")
absent("FAIL", "S10", RA, r'STRICT.*!=\s*"?1"?|\$\{?HYPATIAX_STRICT\}?"?\s*!=', "no assertion STRICT==1")
find("WARN", "S11", RA, r"will produce null extrap_r2_far", None, "stale warning: extrap module is inlined")
# Suppressions inventory
cnt = collections.Counter()
for p in glob.glob("hypatiax/**/*.py", recursive=True) + glob.glob("scripts/**/*.py", recursive=True):
    for i, l in enumerate(lines(p) or [], 1):
        m = re.search(r"audit:\s*ignore\[(\w+)\]", l)
        if m:
            cnt[m.group(1)] += 1
            if not re.search(r"audit:\s*ignore\[\w+\]\s*\S", l.split("ignore[")[1].split("]", 1)[1] if "]" in l else ""):
                results.append(("WARN", "S12", p, i, "suppression without a reason"))
results.append(("INFO", "S12", "(all)", 0, f"suppressions by code: {dict(cnt)}"))
# Unseeded randomness in generators
find("WARN", "S13", "hypatiax/tools/symbolic/physics_aware_regressor.py", r"np\.random\.uniform\(", None,
     "unseeded? confirm routed through seed audit")

order = {"FAIL": 2, "WARN": 1, "INFO": 0}
for sev, cid, f, n, t in sorted(results, key=lambda r: (order[r[0]], r[1], r[2], r[3])):
    print(f"{sev:4s} {cid} {f}:{n} {t}")
nf = sum(r[0] == "FAIL" for r in results)
print(f"\nRESULT: {'FAILED' if nf else 'ok'} ({nf} FAIL, {sum(r[0]=='WARN' for r in results)} WARN)")
sys.exit(1 if nf else 0)
