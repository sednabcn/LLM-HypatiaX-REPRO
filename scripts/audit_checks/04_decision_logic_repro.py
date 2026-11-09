#!/usr/bin/env python3
"""Reproduce the None / nan handling bugs in hybrid_predict (lines ~836-957) with the
EXACT expressions from the source, then show the proposed fix. No repo imports needed.
Exit 1 while the ORIGINAL expressions still misbehave (documents the bug); the FIXED
variant must pass every case or the script exits 2."""
import math, sys
import numpy as np


def orig_state(m):
    llm_r2 = m.get("r2", 0) if m.get("success") else -np.inf
    llm_ok = m.get("success", False) and np.isfinite(llm_r2) and llm_r2 > 0
    return llm_r2, llm_ok


def fixed_state(m):
    r2 = m.get("r2")
    if not m.get("success") or r2 is None or not math.isfinite(r2):
        return -math.inf, False
    return r2, r2 > 0


def decide(llm_ok, llm_r2, nn_r2):
    # mirrors lines 896 / 906 / fallthrough
    if llm_ok and llm_r2 >= nn_r2:
        return "llm"
    if llm_ok and nn_r2 > llm_r2 and nn_r2 > 0.90:
        return "blend"
    return "nn_fallback"


def decide_fixed(llm_ok, llm_r2, nn_r2):
    if not (nn_r2 is not None and math.isfinite(nn_r2)):
        return "llm" if llm_ok else "fail"      # explicit nan/None NN branch
    return decide(llm_ok, llm_r2, nn_r2)


cases = [
    ("llm ok, nn ok", {"success": True, "r2": 0.95}, 0.80, "llm"),
    ("llm r2=None (PHASE1-FIX), nn ok", {"success": True, "r2": None}, 0.80, "nn_fallback"),
    ("llm failed", {"success": False, "r2": None}, 0.80, "nn_fallback"),
    ("llm ok, nn=nan", {"success": True, "r2": 0.60}, float("nan"), "llm"),
    ("llm ok, nn=None", {"success": True, "r2": 0.60}, None, "llm"),
    ("both fail, nn=nan", {"success": False}, float("nan"), "fail"),
]
bad_orig = bad_fixed = 0
for name, m, nn, want in cases:
    try:
        st = orig_state(m)
        got = decide(st[1], st[0], nn)
        o = f"{got}" + ("" if got == want else f"  <-- expected {want}")
        bad_orig += got != want
    except Exception as e:
        o = f"RAISES {type(e).__name__}"
        bad_orig += 1
    try:
        st = fixed_state(m)
        got = decide_fixed(st[1], st[0], nn)
        f = got if got == want or (want == "nn_fallback" and got in ("fail", "nn_fallback")) else f"{got} <-- expected {want}"
        ok = got == want or (want == "nn_fallback" and got in ("fail", "nn_fallback"))
        bad_fixed += not ok
    except Exception as e:
        f = f"RAISES {type(e).__name__}"
        bad_fixed += 1
    print(f"{name:36s} original: {o:40s} fixed: {f}")
print(f"\noriginal misbehaves in {bad_orig} cases; fixed in {bad_fixed}")
print("""
Proposed patch (hybrid_predict, replace lines 837-838):
    _r2 = llm_metrics.get("r2")
    llm_ok = bool(llm_metrics.get("success")) and _r2 is not None and np.isfinite(_r2) and _r2 > 0
    llm_r2 = _r2 if llm_ok or (_r2 is not None and np.isfinite(_r2)) else -np.inf
and add before the decision block:
    if nn_r2 is None or not np.isfinite(nn_r2):   # explicit branch, record reason='nn_nonfinite'
        decision, reason = ("llm", "NN non-finite") if llm_ok else ("fail", "both failed")
""")
sys.exit(2 if bad_fixed else (1 if bad_orig else 0))
