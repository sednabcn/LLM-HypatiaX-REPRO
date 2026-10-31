"""Regression: P6 (G1 dry check) must reproduce every P-arm data hash, per seed, with zero mismatches.

Each seed runs in a fresh interpreter because NumPy fixes its SIMD kernel dispatch at first import;
the pin lives at the top of scripts/phase3_all.py and must be applied before numpy loads.
No API calls are made.
"""
import glob
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ROWS = sorted(glob.glob(str(ROOT / "archive/phase2/p2/pure_llm_seed*.jsonl")))

CHILD = textwrap.dedent("""
    import json, sys, importlib
    sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
    import phase3_all as P3            # applies the numpy pin before numpy is imported
    import phase3_engine_adapter as A
    exp1 = importlib.import_module(A.EXP1_MODULE)
    ok, detail = P3._avx512_state()
    seed, files = int(sys.argv[1]), sys.argv[2:]
    rows = [r for f in files for r in P3.read_jsonl(f) if int(r["seed"]) == seed]
    bad = []
    for r in rows:
        eq = next(e for e in exp1.CORE_15 if e["name"] == r["equation"])
        es = seed + exp1.EQ_ID[eq["name"]] * 7
        with A._rng_isolated():
            X, _, y, _, _, _ = exp1.generate_data(eq, N=200, noise_level=0.05, seed=es)
            Xf, yf = exp1.generate_extrap_data(eq, regime="far", N=100, seed=es)
        if P3.hash_arrays(X, y) != r["train_data_sha256"] or P3.hash_arrays(Xf, yf) != r["far_data_sha256"]:
            bad.append(r["equation"])
    print(json.dumps({"pin_ok": ok, "detail": detail, "n": len(rows), "bad": bad}))
""")


@pytest.mark.skipif(not ROWS, reason="Phase 2 P rows not present")
@pytest.mark.parametrize("seed", [42, 99, 123])
def test_p6_hashes_match_for_seed(seed):
    out = subprocess.run([sys.executable, "-c", CHILD, str(seed), *ROWS], cwd=ROOT,
                         capture_output=True, text=True, timeout=600)
    assert out.returncode == 0, out.stderr[-2000:]
    res = json.loads(out.stdout.strip().splitlines()[-1])
    assert res["pin_ok"], res["detail"]
    assert res["n"] == 15, f"expected 15 equations for seed {seed}, got {res['n']}"
    assert res["bad"] == [], f"hash mismatches at seed {seed}: {res['bad']}"
