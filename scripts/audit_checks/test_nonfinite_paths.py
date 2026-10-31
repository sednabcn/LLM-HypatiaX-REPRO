import os
import numpy as np
from hypatiax.core.generation.hybrid_all_domains_llm_nn.hybrid_system_llm_nn_all_domains import HybridSystemAllDomains

os.environ["HYPATIAX_HOLDOUT"] = "0"
rng = np.random.default_rng(0)
X = rng.uniform(0.5, 3.0, size=(200, 2))
y = X[:, 0] ** 2 * X[:, 1]

GOOD = {"formula": "a**2*b", "python_code": "def f(a, b):\n    return a**2 * b\n",
        "llm_source": "stub", "llm_called": False, "bypass_kind": "stub"}
BAD = {"error": "stub failure", "formula": "", "python_code": "",
       "llm_source": "stub", "llm_called": False, "bypass_kind": "stub"}

def run(llm, nn_r2, tag):
    h = HybridSystemAllDomains.__new__(HybridSystemAllDomains)
    h.generate_llm_formula = lambda *a, **k: dict(llm)
    h.train_nn = lambda X, y, epochs=1000, seed=None: (None, {"r2": nn_r2, "rmse": None})
    r = h.hybrid_predict("nf " + tag, "physics", X, y, ["a", "b"], {}, verbose=False)
    print(f"{tag:28s} decision={r['decision']:5s} r2={r['evaluation'].get('r2')} reason={r.get('decision_reason')}")
    return r

# LLM good, NN failed (None) or undefined (nan): the LLM must win, no crash
assert run(GOOD, None, "llm ok, nn None")["decision"] == "llm"
assert run(GOOD, float("nan"), "llm ok, nn nan")["decision"] == "llm"

# LLM failed (r2 None internally): a finite NN must be used, a failed NN must give "fail"
assert run(BAD, 0.5, "llm failed, nn 0.5")["decision"] == "nn"
r = run(BAD, None, "llm failed, nn None")
assert r["decision"] == "fail"
r2 = r["evaluation"].get("r2")
assert r2 is None or not np.isfinite(r2) or r2 < 0, f"failed row must not look like a pass: r2={r2}"
r = run(BAD, float("nan"), "llm failed, nn nan")
assert r["decision"] == "fail"
print("PASS")
