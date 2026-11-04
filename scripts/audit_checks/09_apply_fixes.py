#!/usr/bin/env python3
"""Apply the DECIDED code fixes with exact-line matching. Dry run (diffs only) by default.

  python3 09_apply_fixes.py                 # show diffs
  python3 09_apply_fixes.py --apply         # write, then py_compile / bash -n
  python3 09_apply_fixes.py --only F1,F2    # subset      --root DIR  (default .)

A fix is skipped (and nothing is written for that file) unless its target text is found
exactly once, so a drifted file is never half-patched.
F1 llm_r2/llm_ok None-safe       F2 nn_r2 nan/None -> failure (-inf), never wins or blends
F3 NN failure metrics r2 None    F4 missing r2 is a failure, not 0.0
F5 assert HYPATIAX_STRICT==1     F6 drop call to deleted analyze_hybrid_performance.py (suppA)
Not here (needs a decision): audit_paper/paper_targets.json, merge_extrap block, workflows.
"""
import argparse, difflib, pathlib, py_compile, subprocess, sys

HY = "hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py"
V2 = "hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py"
RA = "run_all.sh"


def line_fix(old, new):
    """Replace the single line whose stripped text == old by `new` lines (indent preserved)."""
    def f(text):
        ls = text.split("\n")
        idx = [i for i, l in enumerate(ls) if l.strip() == old]
        if len(idx) != 1:
            raise ValueError(f"expected exactly 1 line == {old!r}, found {len(idx)}")
        i = idx[0]
        ind = ls[i][: len(ls[i]) - len(ls[i].lstrip())]
        ls[i:i + 1] = [ind + n for n in new]
        return "\n".join(ls)
    return f


def block_fix(old, new):
    def f(text):
        if text.count(old) != 1:
            raise ValueError(f"expected exactly 1 block, found {text.count(old)}")
        return text.replace(old, new)
    return f


FIXES = {
    "F1": [(HY, line_fix('llm_r2 = llm_metrics.get("r2", 0) if llm_metrics.get("success") else -np.inf',
                         ['llm_r2 = llm_metrics.get("r2") if llm_metrics.get("success") else None'])),
           (HY, line_fix('llm_ok = llm_metrics.get("success", False) and np.isfinite(llm_r2) and llm_r2 > 0',
                         ['llm_ok = bool(llm_metrics.get("success")) and llm_r2 is not None and np.isfinite(llm_r2) and llm_r2 > 0',
                          'if llm_r2 is None or not np.isfinite(llm_r2):',
                          '    llm_r2 = -np.inf   # failure sentinel (r2_canonical convention): never wins, never blends']))],
    "F2": [(HY, line_fix('nn_r2 = nn_metrics.get("r2", 0)',
                         ['nn_r2 = nn_metrics.get("r2")',
                          'if nn_r2 is None or not np.isfinite(nn_r2):',
                          '    nn_r2 = -np.inf   # non-finite NN = failure: never wins, never blends']))],
    "F3": [(HY, line_fix('"nn_result": {"metrics": {"r2": 0.0, "rmse": None, "mae": None, "reason": "nonfinite_metric"}},',
                         ['"nn_result": {"metrics": {"r2": None, "rmse": None, "mae": None, "reason": "nonfinite_metric"}},']))],
    "F4": [(V2, line_fix('r2_val   = float(eval_.get("r2", 0.0))',
                         ['r2_val   = eval_.get("r2")',
                          'if r2_val is None:',
                          '    return self._unavailable("evaluation has no r2")',
                          'r2_val   = float(r2_val)']))],
    "F5": [(RA, line_fix('export HYPATIAX_STRICT="${HYPATIAX_STRICT:-1}"',
                         ['export HYPATIAX_STRICT="${HYPATIAX_STRICT:-1}"',
                          '[[ "${HYPATIAX_STRICT}" == "1" ]] || { echo "ERROR: HYPATIAX_STRICT must be 1 for the controlled run" >&2; exit 1; }']))],
    "F6": [(RA, block_fix(
        "  python3 hypatiax/analysis/analyze_hybrid_performance.py \\\n"
        "    --results-dir '${RESULTS_DIR}' \\\n"
        "    2>&1 | tee -a '${RESULTS_DIR}'/suppA_run.log\n",
        "  echo '[suppA] analyze_hybrid_performance.py was removed from the repo (78e4244); skipping'\n"))],
}

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--only", default="")
ap.add_argument("--root", default=".")
a = ap.parse_args()
root = pathlib.Path(a.root)
want = [x for x in a.only.split(",") if x] or list(FIXES)

orig, new, failed_paths, ok = {}, {}, set(), []
for fid in want:
    for path, fn in FIXES[fid]:
        p = root / path
        if not p.exists():
            print(f"{fid}: SKIP missing {path}"); failed_paths.add(path); continue
        orig.setdefault(path, p.read_text())
        cur = new.get(path, orig[path])
        try:
            new[path] = fn(cur)
        except ValueError as e:
            print(f"{fid}: SKIP {path}: {e}"); failed_paths.add(path); continue
        ok.append(fid)

for path in new:
    if new[path] == orig[path]:
        continue
    print("".join(difflib.unified_diff(orig[path].splitlines(True), new[path].splitlines(True),
                                       f"a/{path}", f"b/{path}", n=1)))
print("fixes matched:", sorted(set(ok)), "| files with a skipped fix:", sorted(failed_paths) or "none")

if a.apply:
    bad = 0
    for path, text in new.items():
        if path in failed_paths:
            print(f"NOT written (a fix for it was skipped): {path}"); continue
        (root / path).write_text(text)
        print("written", path)
        if path.endswith(".py"):
            try:
                py_compile.compile(str(root / path), doraise=True)
            except py_compile.PyCompileError as e:
                print("COMPILE ERROR", e); bad = 1
        elif path.endswith(".sh"):
            bad |= subprocess.call(["bash", "-n", str(root / path)])
    sys.exit(bad)
else:
    print("dry run; add --apply to write")
