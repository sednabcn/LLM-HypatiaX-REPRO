#!/usr/bin/env python3
"""Self-test of hypatiax.core.r2_canonical + fragility scan of benchmark targets (L07/L08 support).

Usage: python3 03_r2_policy_selftest.py [targets.csv|.npy|.npz ...]
For files, y is the LAST column (csv) / array 'y' (npz) / the array itself (1-D npy).
Flags targets with ss_tot/sum(y^2) < 1e-10 (R^2 numerically unreliable though status 'ok').
Run from the repo root. Exit 1 if a policy assertion fails."""
import os, sys
import numpy as np

sys.path.insert(0, ".")
os.environ.pop("HYPATIAX_R2_SIGN_FLIP", None)
from hypatiax.core import r2_canonical as rc  # noqa: E402

fails = []


def check(name, cond, info=""):
    print(("ok   " if cond else "FAIL ") + name, info)
    if not cond:
        fails.append(name)


rng = np.random.default_rng(0)
y = rng.normal(size=200)
v, s = rc.r2_scored(y, y)
check("perfect prediction -> 1.0", abs(v - 1) < 1e-12 and s == "ok", (v, s))
v, s = rc.r2_scored(np.ones(50), np.ones(50))
check("constant target -> nan degenerate", np.isnan(v) and s == "degenerate_target", (v, s))
v, s = rc.r2_scored(y, np.where(np.arange(200) == 3, np.nan, y))
check("nan prediction -> -inf", v == -np.inf, (v, s))
v, s = rc.r2_scored(y, y * 1e101)
check("|pred|>1e100 -> -inf", v == -np.inf and s == "pred_out_of_range", (v, s))
v, s = rc.r2_scored(y, y + 1e3)
check("R2 < -100 -> -inf catastrophic", v == -np.inf and s == "catastrophic", (v, s))
v, s = rc.r2_scored(y, -y)
check("sign flip OFF by default (R2(-y) stays negative)", v < 0, (v, s))
v2, _ = rc.r2_scored(y, -y, sign_flip=True)
check("sign flip only when explicitly requested", v2 > v, (v, v2))
check("sign_flip_enabled() False without env", not rc.sign_flip_enabled())
check("no ss_tot copies drift: r2_checked == r2_scored on benign data",
      rc.r2_checked(y, y * 0.9)[0] == rc.r2_scored(y, y * 0.9)[0])

# offset fragility demo
yo = 1e6 + rng.normal(scale=1e-3, size=200)
ratio = float(np.sum((yo - yo.mean()) ** 2) / np.sum(yo ** 2))
v, s = rc.r2_scored(yo, yo + rng.normal(scale=1e-4, size=200))
print(f"info offset target: ss_tot/sum(y^2)={ratio:.2e}, status={s}, R2={v:.4f} (status 'ok' but cancellation-prone)")


def load(p):
    if p.endswith(".npz"):
        d = np.load(p)
        return np.asarray(d["y"] if "y" in d else d[d.files[-1]], float).ravel()
    if p.endswith(".npy"):
        a = np.load(p)
        return np.asarray(a if a.ndim == 1 else a[:, -1], float).ravel()
    try:
        a = np.loadtxt(p, delimiter=",")
    except ValueError:
        a = np.loadtxt(p, delimiter=",", skiprows=1)
    return np.asarray(a if a.ndim == 1 else a[:, -1], float).ravel()


frag = 0
for p in sys.argv[1:]:
    try:
        t = load(p)
        r = float(np.sum((t - t.mean()) ** 2) / max(np.sum(t ** 2), 1e-300))
        flag = r < 1e-10
        frag += flag
        print(f"{'FRAGILE' if flag else 'ok     '} {p}: ss_tot/sum(y^2)={r:.2e} n={t.size}")
    except Exception as e:
        print(f"skip {p}: {e}")
print(f"\nfragile targets: {frag}; policy assertion failures: {len(fails)}")
sys.exit(1 if fails else 0)
