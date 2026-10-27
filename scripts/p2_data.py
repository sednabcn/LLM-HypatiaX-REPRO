# scripts/p2_data.py
from hypatiax.experiments.benchmarks import exp1_ablation as E

# Neutral task text for the Pure LLM arm (P). HDS's clean-mode string
# ("(withheld - infer the relationship from the data patterns)") refers to data
# patterns that P does not receive, so P gets a neutral wording instead.
# Declare this wording difference alongside the data-statistics asymmetry.
DESCRIPTION = "Find the formula for the target quantity as a function of the listed variables."

# The HDS prompt (symbolic_engine.py _build_prompt) always sends this constants
# block, with ROUNDED values. The repo's PHYSICAL_CONSTANTS holds exact CODATA
# values (e.g. c=299792458.0), so it must NOT be passed through: P would see
# more precise numbers than HDS. Hard-code the HDS block instead.
HDS_PROMPT_CONSTANTS = {
    "h": 6.626e-34, "hbar": 1.055e-34, "c": 2.998e8,
    "k_B": 1.381e-23, "k": 1.381e-23, "N_A": 6.022e23, "g_n": 9.807,
    "m_e": 9.109e-31, "q_e": 1.602e-19,
    "epsilon0": 8.854e-12, "mu0": 1.257e-6,
}
USE_CONSTANTS = True

_EQ = {e["name"]: e for e in E.CORE_15}


def generate_case(equation, seed):
    if DESCRIPTION is None or USE_CONSTANTS is None:
        raise RuntimeError("set DESCRIPTION and USE_CONSTANTS in p2_data.py first")
    eq = _EQ[equation]
    eq_seed = seed + E.EQ_ID.get(equation, 0) * 7
    X_train, _, y_train, _, _, _ = E.generate_data(eq, N=200, noise_level=0.05, seed=eq_seed)
    safe, _ = E.VariableNameSanitizer().sanitize(eq["vars"])
    out = {"X_train": X_train, "y_train": y_train, "variable_names": list(safe),
           "domain": eq["domain"].lower().replace(" ", "_"),
           "description": DESCRIPTION,
           "constants": dict(HDS_PROMPT_CONSTANTS) if USE_CONSTANTS else {}}
    for regime in ("near", "medium", "far"):
        Xe, ye = E.generate_extrap_data(eq, regime=regime, N=100, seed=eq_seed)
        out[f"X_{regime}"], out[f"y_{regime}"] = Xe, ye
    return out
