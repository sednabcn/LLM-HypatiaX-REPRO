"""
Example: how a hybrid system should call train_nn_model()/nn_predict() from
hybrid_system_nn_defi_domain.py, combine the result with an LLM-produced
formula, and form an uncertainty-weighted ensemble.

This snippet assumes these modules are available in your PYTHONPATH:
- baseline_pure_llm_defi_discovery.PureLLMBaseline (or another LLM wrapper)
- hybrid_system_nn_defi_domain.{train_nn_model, nn_predict}
- hypatiax.core.metrics (the single shared evaluator)

Contributes uncertainty-weighted ensemble combining LLM + NN:

ensemble_llm_nn() - Weights predictions by inverse uncertainty
Better than choosing one method outright
Could help when both methods are valid but imperfect

CHANGES (B2 / B3 / B4 / C4 re-run plan)
---------------------------------------
B2  Provenance. Every run now records llm_called, bypass_kind, bypass_flags,
    formula_present and the formula/python_code strings, copied from the
    shared PureLLMBaseline.generate_formula() result. The canonical Kelly
    fallback is itself a ground-truth leak, so it is labelled
    bypass_kind="canonical_fallback" and is DISABLED when both
    HYPATIAX_DISABLE_HARDCODED=1 and HYPATIAX_DISABLE_PROMPT_HINTS=1 are set
    (a clean live run must not silently substitute the answer).
B3  One evaluator. R² now comes from hypatiax.core.metrics.compute_r2 for the
    LLM, NN, ensemble and chosen method, instead of sklearn's r2_score
    (which raises on NaN and silently turned a failed LLM into "no LLM").
C4  Non-finite LLM predictions are recorded as failures (r2=NaN), not dropped.
B4  No test leakage. The ensemble weights and the method choice are computed
    from a TRAIN split only; the reported R² is on a held-out TEST split.
    (Previously the NN was trained and scored on the same rows and the
    weights/choice used the very rows being reported.)
Exec  The LLM code is now executed in ONE namespace, so module-level
    constants and helper functions resolve, and the function named
    ``formula`` is preferred over "first callable found" (which used to pick
    a helper, or even the injected ``exp`` lambda).
"""

import argparse
import hashlib
import json
import math
import os
import types

import numpy as np

# Import your LLM baseline and NN baseline implementations
from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import PureLLMBaseline
from hypatiax.core.metrics import compute_r2  # shared evaluator (B3)
from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
# NOTE: the trainable NN lives in hybrid_system_nn_defi_domain.py as plain
# functions (train_nn_model, nn_predict). The import is deferred into main()
# purely so this module's NN-independent functions
# (execute_python_code_get_predictions, ensemble_llm_nn) stay importable
# even if the NN module or its torch dependency is unavailable.


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def strict_live_mode() -> bool:
    """True when BOTH bypass switches are off -> a clean, live-LLM-only run."""
    return _flag("HYPATIAX_DISABLE_HARDCODED") and _flag("HYPATIAX_DISABLE_PROMPT_HINTS")


def _score(x) -> float:
    """Sortable score: None/NaN -> -inf so failures never win a comparison."""
    return -math.inf if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


# ---------------------------------------------------------------------------
# LLM code execution
# ---------------------------------------------------------------------------
def execute_python_code_get_predictions(python_code: str, X: np.ndarray):
    """
    Exec the python_code string and return vectorized predictions for X.

    The code must define a function named ``formula``; if it does not, the
    LAST function defined by the code is used. Raises RuntimeError on exec
    failure, no function, wrong output length, or any NaN/inf prediction.
    """
    import math as _math
    ns = {
        "np":      np,
        "numpy":   np,
        "math":    _math,
        "pi":      np.pi,
        "e":       np.e,
        "exp":     lambda x: np.exp(np.clip(x, -500.0, 500.0)),
        "log":     np.log,
        "log2":    np.log2,
        "log10":   np.log10,
        "sqrt":    np.sqrt,
        "sin":     np.sin,
        "cos":     np.cos,
        "tan":     np.tan,
        "arcsin":  lambda x: np.arcsin(np.clip(x, -1.0, 1.0)),
        "arccos":  lambda x: np.arccos(np.clip(x, -1.0, 1.0)),
        "arctan":  np.arctan,
        "arctan2": np.arctan2,
        "abs":     np.abs,
        "sign":    np.sign,
        "tanh":    np.tanh,
        "sinh":    np.sinh,
        "cosh":    np.cosh,
        "minimum": np.minimum,
        "maximum": np.maximum,
        "clip":    np.clip,
    }
    preloaded = set(ns)
    try:
        # Single namespace (globals only): module-level constants and helper
        # functions defined by the LLM stay visible inside ``formula``.
        exec(python_code, ns)
    except Exception as e:
        raise RuntimeError(f"Exec failed: {e}\nCode preview:\n{python_code[:400]}")

    func = ns.get("formula") if callable(ns.get("formula")) else None
    if func is None:
        defined = [
            v for k, v in ns.items()
            if k not in preloaded and isinstance(v, types.FunctionType)
        ]
        func = defined[-1] if defined else None
    if func is None:
        raise RuntimeError("No function found in executed LLM code")

    n = X.shape[0]
    with np.errstate(all="ignore"):
        if X.ndim == 1 or X.shape[1] == 1:
            y_pred = func(X[:, 0] if X.ndim > 1 else X)
        else:
            args = [X[:, i] for i in range(X.shape[1])]
            try:
                y_pred = func(*args)
            except Exception:
                # fallback row-by-row
                y_pred = np.array([func(*X[i, :]) for i in range(n)])

    y_pred = np.asarray(y_pred, dtype=float).flatten()
    if y_pred.size == 1 and n > 1:  # constant formula -> broadcast
        y_pred = np.full(n, y_pred[0])
    if y_pred.size != n:
        raise RuntimeError(f"Prediction length {y_pred.size} != n_samples {n}")
    if not np.all(np.isfinite(y_pred)):
        bad = int(np.sum(~np.isfinite(y_pred)))
        raise RuntimeError(f"Non-finite predictions ({bad}/{n} NaN/inf)")
    return y_pred


# ---------------------------------------------------------------------------
# Ensemble
# ---------------------------------------------------------------------------
def _rmse(pred, y):
    return float(np.sqrt(np.mean((np.asarray(pred) - np.asarray(y)) ** 2)))


def ensemble_llm_nn(llm_pred, nn_pred, y_true, llm_r2=None, nn_r2=None,
                    weight_data=None):
    """
    Build an uncertainty-weighted ensemble between LLM and NN predictions.
    - Uncertainty = RMSE of residuals (std of residuals ignored constant bias,
      so an LLM formula with a large offset looked artificially certain)
    - Weight = inverse uncertainty, optionally scaled by R² (clipped at 0)

    weight_data : optional (llm_pred_fit, nn_pred_fit, y_fit)
        If given, weights are fitted on THIS data (the train split) and then
        applied to ``llm_pred`` / ``nn_pred`` (the test split). If omitted,
        weights are fitted on y_true itself (in-sample; legacy behaviour).
    llm_r2 / nn_r2 should then also come from the fit data.
    """
    eps = 1e-8
    f_llm, f_nn, f_y = weight_data if weight_data is not None else (llm_pred, nn_pred, y_true)

    llm_ok = (
        llm_pred is not None and f_llm is not None
        and np.all(np.isfinite(llm_pred)) and np.all(np.isfinite(f_llm))
    )
    if not llm_ok:
        llm_pred = None

    llm_unc = _rmse(f_llm, f_y) if llm_ok else 1.0
    nn_unc = _rmse(f_nn, f_y)

    llm_strength = float(llm_r2) if (llm_r2 is not None and not math.isnan(llm_r2)) else 1.0
    nn_strength = float(nn_r2) if (nn_r2 is not None and not math.isnan(nn_r2)) else 1.0

    w_llm = (1.0 / (llm_unc + eps)) * max(llm_strength, 0.0) if llm_ok else 0.0
    w_nn = (1.0 / (nn_unc + eps)) * max(nn_strength, 0.0)

    if w_llm + w_nn <= 0:
        # fallback equal weights
        w_llm = 0.5 if llm_ok else 0.0
        w_nn = 0.5 if llm_ok else 1.0

    total = w_llm + w_nn
    w_llm /= total
    w_nn /= total

    ensemble = nn_pred if llm_pred is None else w_llm * llm_pred + w_nn * nn_pred

    return ensemble, {
        "w_llm": w_llm,
        "w_nn": w_nn,
        "llm_unc": llm_unc,
        "nn_unc": nn_unc,
    }


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------
def split_indices(n: int, seed: int, test_frac: float = 0.2):
    """Seeded train/test index split (same seed -> same split)."""
    if n < 5:
        raise ValueError(f"Need at least 5 samples to split, got {n}")
    perm = np.random.default_rng(seed).permutation(n)
    n_test = max(1, int(round(n * test_frac)))
    return np.sort(perm[n_test:]), np.sort(perm[:n_test])


# ---------------------------------------------------------------------------
# Demo / run
# ---------------------------------------------------------------------------
CANONICAL_KELLY = """
def formula(expected_fee_apy, il_risk):
    risk_aversion = 2.0
    f_star = expected_fee_apy / (risk_aversion * il_risk**2)
    return np.minimum(f_star, 1.0)
"""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="write the provenance/result record as JSON")
    args = ap.parse_args(argv)

    protocol = DeFiExperimentProtocol()
    cases = protocol.load_test_data("liquidity", num_samples=100)
    target = None
    for desc, X, y_true, var_names, meta in cases:
        if "kelly" in desc.lower() or "optimal lp" in desc.lower():
            target = (desc, X, y_true, var_names, meta)
            break
    desc, X, y_true, var_names, meta = target if target is not None else cases[0]

    print("Selected test:", desc)
    print("Variables:", var_names)
    print("Data shapes:", X.shape, y_true.shape)

    seed = int(hashlib.sha256(desc.encode()).hexdigest(), 16) % (2**31)
    tr, te = split_indices(len(y_true), seed)
    X_tr, X_te, y_tr, y_te = X[tr], X[te], y_true[tr], y_true[te]
    print(f"Split: train={len(tr)} test={len(te)} (seed={seed})")

    strict = strict_live_mode()
    print("Strict live mode (both bypass flags off):", strict)

    # 1) Generate/obtain LLM formula
    llm_error = None
    try:
        llm = PureLLMBaseline()
        llm_result = llm.generate_formula(
            description=desc,
            domain="liquidity",
            variable_names=var_names,
            metadata=meta,
        )
    except Exception as e:  # no API key / call failed / constructor raised
        llm_error = f"{type(e).__name__}: {e}"
        llm_result = {"python_code": "N/A", "formula": "N/A"}
        print("LLM call failed or unavailable:", llm_error)

    # Provenance copied from the shared generator (B2). Older generator
    # versions may not set these -> None means "unknown", never assumed live.
    prov = {
        "llm_called":    llm_result.get("llm_called"),
        "bypass_kind":   llm_result.get("bypass_kind"),
        "bypass_flags":  llm_result.get("bypass_flags"),
        "stop_reason":   llm_result.get("stop_reason"),
        "usage":         llm_result.get("usage"),
        "llm_error":     llm_error,
    }

    no_code = not llm_result.get("python_code") or llm_result.get("python_code") == "N/A"
    if no_code and not strict:
        # The canned Kelly answer is a ground-truth leak: label it.
        llm_result = {"python_code": CANONICAL_KELLY, "formula": "min(mu/(lambda*sigma^2),1.0)"}
        prov.update(llm_called=False, bypass_kind="canonical_fallback")
        print("Using canonical fallback (labelled bypass_kind=canonical_fallback).")
    elif no_code and strict:
        print("Strict live mode: no canonical fallback; LLM arm recorded as failed.")

    # 2) Evaluate LLM formula on train and test with the shared evaluator
    llm_pred_tr = llm_pred_te = None
    llm_r2_tr = llm_r2_te = float("nan")
    llm_fail = None
    try:
        llm_pred_tr = execute_python_code_get_predictions(llm_result["python_code"], X_tr)
        llm_pred_te = execute_python_code_get_predictions(llm_result["python_code"], X_te)
        llm_r2_tr = compute_r2(y_tr, llm_pred_tr)
        llm_r2_te = compute_r2(y_te, llm_pred_te)
        print(f"LLM R² train={llm_r2_tr:.6f} test={llm_r2_te:.6f}")
    except Exception as e:
        llm_fail = str(e).splitlines()[0]
        llm_pred_tr = llm_pred_te = None
        print("LLM evaluation failure (recorded, r2=NaN):", llm_fail)

    # 3) Train NN on TRAIN only
    from hybrid_system_nn_defi_domain import train_nn_model, nn_predict

    model, scaler_X, scaler_y = train_nn_model(
        X_tr, y_tr, hidden_dims=[128, 64, 32], epochs=200, seed=seed
    )
    nn_pred_tr = nn_predict(model, scaler_X, scaler_y, X_tr)
    nn_pred_te = nn_predict(model, scaler_X, scaler_y, X_te)
    nn_r2_tr = compute_r2(y_tr, nn_pred_tr)
    nn_r2_te = compute_r2(y_te, nn_pred_te)
    print(f"NN  R² train={nn_r2_tr:.6f} test={nn_r2_te:.6f}")

    # 4) Ensemble: weights fitted on TRAIN, applied to TEST
    ens_te, info = ensemble_llm_nn(
        llm_pred_te, nn_pred_te, y_te,
        llm_r2=llm_r2_tr if llm_pred_tr is not None else None,
        nn_r2=nn_r2_tr,
        weight_data=(llm_pred_tr, nn_pred_tr, y_tr),
    )
    ens_tr, _ = ensemble_llm_nn(
        llm_pred_tr, nn_pred_tr, y_tr,
        llm_r2=llm_r2_tr if llm_pred_tr is not None else None, nn_r2=nn_r2_tr,
    )
    ens_r2_tr = compute_r2(y_tr, ens_tr)
    ens_r2_te = compute_r2(y_te, ens_te)
    print("Ensemble info:", info)
    print(f"Ensemble R² train={ens_r2_tr:.6f} test={ens_r2_te:.6f}")

    # 5) Method choice uses TRAIN scores only; the reported number is TEST.
    if llm_pred_tr is not None and _score(llm_r2_tr) > 0.95:
        chosen, chosen_te = "LLM", llm_pred_te
    elif _score(ens_r2_tr) > max(_score(nn_r2_tr), _score(llm_r2_tr)):
        chosen, chosen_te = "ENSEMBLE", ens_te
    else:
        chosen, chosen_te = "NN", nn_pred_te
    chosen_r2_te = compute_r2(y_te, chosen_te)
    print("Chosen method (picked on train):", chosen)
    print(f"Chosen R² (test): {chosen_r2_te:.6f}")

    record = {
        "description": desc,
        "seed": seed,
        "n_train": int(len(tr)),
        "n_test": int(len(te)),
        "strict_live": strict,
        "formula": llm_result.get("formula"),
        "python_code": llm_result.get("python_code"),
        "formula_present": bool(llm_result.get("formula") not in (None, "", "N/A")),
        **prov,
        "llm_eval_error": llm_fail,
        "r2_test": {"llm": llm_r2_te, "nn": nn_r2_te,
                    "ensemble": ens_r2_te, "chosen": chosen_r2_te},
        "r2_train": {"llm": llm_r2_tr, "nn": nn_r2_tr, "ensemble": ens_r2_tr},
        "chosen_method": chosen,
        "ensemble_info": info,
    }
    if args.out:
        with open(args.out, "w") as f:
            json.dump(record, f, indent=2, default=str)
        print("Wrote", args.out)
    return record


if __name__ == "__main__":
    main()
