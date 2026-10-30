"""Stand-in for PySRRegressor that rejects unsupported guess operators the way Julia does.

Run from the repo root:  python fake_probe.py
"""
import re
import sys
import types

import numpy as np
import pandas as pd

sys.path.insert(0, ".")


class FakePySR:
    last = None

    def __init__(self, model_selection="best", binary_operators=None, unary_operators=None,
                 niterations=1, guesses=None, **kw):
        self.kw = dict(kw, binary_operators=binary_operators,
                       unary_operators=unary_operators, guesses=guesses)
        self.guesses = guesses
        self.binary = binary_operators or []
        self.unary = unary_operators or []
        FakePySR.last = self

    def fit(self, X, y, variable_names=None, **kw):
        allowed_fns = {n.split("(")[0] for n in self.unary} | {n for n in self.binary if n.isidentifier()}
        for g in self.guesses or []:
            for fn in re.findall(r"([A-Za-z_]\w*)\(", g):
                if fn not in allowed_fns:
                    raise RuntimeError(f"JuliaError: ArgumentError: Unrecognized operator: `{fn}`")
            if ("^" in g or "**" in g) and not ({"^", "pow"} & set(self.binary)):
                raise RuntimeError("JuliaError: ArgumentError: Unrecognized operator: `^`")
        self.variable_names = variable_names
        self.equations_ = pd.DataFrame({
            "complexity": [3], "loss": [1e-9], "score": [1.0],
            "equation": ["x0"], "sympy_format": [None], "lambda_format": [None],
        })
        self._X = X

    def predict(self, X, index=None):
        return np.asarray(X)[:, 0]

    def get_best(self):
        return self.equations_.iloc[0]

    def sympy(self, index=None):
        import sympy as sp
        return sp.Symbol("x0")


# Must be installed before the engine imports pysr
mod = types.ModuleType("pysr")
mod.PySRRegressor = FakePySR
sys.modules["pysr"] = mod

import hypatiax.tools.symbolic.symbolic_engine as E  # noqa: E402
from hypatiax.tools.symbolic import guess_sanitizer as G  # noqa: E402

X = np.random.default_rng(0).uniform(1, 3, (60, 1))
y = X[:, 0]


def run(guesses, **kw):
    G.reset_audit()
    # SymbolicEngine requires a config (the original probe omitted it -> TypeError)
    eng = E.SymbolicEngine(E.DiscoveryConfig(niterations=2, pysr_timeout=5))
    res = eng.discover(X, y, ["x0"], equation_name="t", random_state=1,
                       seed_expressions=guesses, **kw)
    return res, G.drain_audit()


if __name__ == "__main__":
    res, row = run(["-x0**2 + 0.16", "sign(x0)", "x0**0.75"])
    print("guess_audit in result:", "guess_audit" in res, "| expr:", res.get("expression"))
    print({k: row[k] for k in ("guesses_requested", "guesses_used", "guesses_dropped",
                               "guess_dropped_reasons", "guess_fit_fallback")})
    print("PySR got guesses:", FakePySR.last.guesses, "| binary:", FakePySR.last.binary)
    # Expected: 1 used, 2 dropped (needs_pow, unsupported_operator:sign), no fit fallback
    assert row["guesses_used"] == 1 and row["guesses_dropped"] == 2
    assert row["guess_fit_fallback"] is False
    print("OK")
