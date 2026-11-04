#!/usr/bin/env python3
"""hybrid_predict: explicit non-finite-NN branch, fixed llm state, honest
fallback reason, success flag. Dry run by default; --apply writes.
Every edit must match exactly once or nothing is written."""
import argparse, difflib, sys
from pathlib import Path

T = Path("hypatiax/core/generation/hybrid_all_domains_llm_nn/"
         "hybrid_system_llm_nn_all_domains.py")

EDITS = []

EDITS.append(("llm state tolerates r2=None",
"""        llm_r2 = llm_metrics.get("r2", 0) if llm_metrics.get("success") else -np.inf
        llm_ok = llm_metrics.get("success", False) and np.isfinite(llm_r2) and llm_r2 > 0
""",
"""        _r2 = llm_metrics.get("r2")
        _llm_scored = bool(llm_metrics.get("success")) and _r2 is not None and np.isfinite(_r2)
        llm_r2 = _r2 if _llm_scored else -np.inf
        llm_ok = _llm_scored and _r2 > 0
"""))

EDITS.append(("explicit non-finite NN branch",
"""        if llm_ok and llm_r2 >= nn_r2:
""",
"""        if not np.isfinite(nn_r2):
            # NN failed (None mapped to -inf above) or undefined (nan):
            # it must never be ranked against the LLM.
            if llm_ok:
                decision = "llm"
                final_r2 = llm_r2
                final_rmse = llm_metrics.get("rmse", float("inf"))
                reason = "NN non-finite; using LLM"
                validation_score = "EXCELLENT" if llm_r2 > 0.95 else "GOOD"
            else:
                decision = "fail"
                final_r2 = nn_r2
                final_rmse = float("inf")
                reason = "both failed"
                validation_score = "POOR"

        elif llm_ok and llm_r2 >= nn_r2:
"""))

EDITS.append(("truthful fallback reason",
"""            reason = "NN fallback (LLM failed)"
""",
"""            reason = (
                "NN fallback (LLM failed)"
                if not llm_ok
                else "NN beats LLM (R2 below blend threshold)"
            )
"""))

EDITS.append(("success flag follows decision",
"""                "rmse": float(final_rmse),
                "success": True,
""",
"""                "rmse": float(final_rmse),
                "success": decision != "fail",
"""))

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

src = T.read_text(encoding="utf-8")
new, bad = src, False
for name, old, repl in EDITS:
    n = new.count(old)
    print("[%s] %s: %d match(es)" % ("ok" if n == 1 else "FAIL", name, n))
    if n != 1:
        bad = True
        continue
    new = new.replace(old, repl)
if bad:
    print("Refusing to write: every edit must match exactly once.")
    sys.exit(2)
sys.stdout.writelines(difflib.unified_diff(
    src.splitlines(True), new.splitlines(True), "a/" + str(T), "b/" + str(T)))
if args.apply:
    T.write_text(new, encoding="utf-8")
    print("applied")
else:
    print("dry run; pass --apply to write")
