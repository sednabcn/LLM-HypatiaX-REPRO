import os
import numpy as np
from hypatiax.core.generation.hybrid_all_domains_llm_nn.hybrid_system_llm_nn_all_domains import HybridSystemAllDomains

h = HybridSystemAllDomains.__new__(HybridSystemAllDomains)
h.generate_llm_formula = lambda *a, **k: {
    "formula": "a**2*b",
    "python_code": "def f(a, b):\n    return a**2 * b\n",
    "llm_source": "stub", "llm_called": False, "bypass_kind": "stub",
}
def _no_nn(*a, **k):
    raise AssertionError("NN must not train under force_llm")
h.train_nn = _no_nn

rng = np.random.default_rng(0)
X = rng.uniform(0.5, 3.0, size=(200, 2))
y = X[:, 0] ** 2 * X[:, 1]

for flag in ("0", "1"):
    os.environ["HYPATIAX_HOLDOUT"] = flag
    r = h.hybrid_predict("force eq", "physics", X, y, ["a", "b"], {"force_llm": True}, verbose=False)
    ev = r["evaluation"]
    assert r["decision"] == "llm"
    assert r["nn_result"]["metrics"]["r2"] is None
    assert r["nn_result"]["metrics"]["reason"] == "skipped_force_llm"
    assert ev["r2"] == ev["r2_in_sample"] == 1.0
    assert "r2_holdout_blend" not in ev        # documented: no NN, no blend, no held-out here
    print("flag", flag, "ok", ev)
print("PASS")
