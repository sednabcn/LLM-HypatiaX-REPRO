"""
phase3_engine_adapter.py - the ONE place that touches the HDS v50_2 engine.  (DRAFT, option 1)

Strategy: call exp1_ablation.run_condition(eq, "hypatia", seed) UNCHANGED, so the full config
is the same code path as the Phase 2 HDS rows.  Gates are switched by setting class attributes
on SymbolicEngineWithLLM (see ENGINE_PATCH below) for the duration of one call, then restoring.

Wired gates (HDS v50_2 has no others):
    llm_acceptance : the "LLM R2 > 0.95 -> skip PySR" shortcut in _discover_hybrid
                     ablated = threshold inf, PySR always runs
    pysr_prior     : seeding PySR's operators/seed_expressions from the LLM candidate
                     ablated = never seed (cold PySR refinement)
Not wired (declare with --omit in phase3_close.py, runner: --components llm_acceptance,pysr_prior):
    probe, nn_augmentation, blend_weight : exist only in hypatiax_defi_benchmark_v3c.py
    complexity_routing : the only complexity gate is `if False and ...` (already off in full)

Three TODOs remain, each marked TODO(...) below.
"""
import contextlib
import hashlib
import math
import os

import numpy as np

# TODO(module): confirm the exact module name of the exp1_ablation file (ls the directory).
EXP1_MODULE = "hypatiax.experiments.benchmarks.exp1_ablation"
ENGINE_MODULE = "hypatiax.tools.symbolic.symbolic_engine"

# name -> (class attribute on SymbolicEngineWithLLM, ablated value).  None = not wired.
GATE_SWITCHES = {
    "llm_acceptance": ("_LLM_ACCEPT_R2", float("inf")),
    "probe": None,
    "complexity_routing": None,
    "nn_augmentation": None,
    "blend_weight": None,
    "pysr_prior": ("_LLM_PRIOR_SEED", False),
}

ENGINE_PATCH = """
In hypatiax/tools/symbolic/symbolic_engine.py, class SymbolicEngineWithLLM, add (un-annotated):
    _LLM_ACCEPT_R2 = 0.95
    _LLM_PRIOR_SEED = True
and in _discover_hybrid change
    if best_hyp.r2_score and best_hyp.r2_score > 0.95:
to  if best_hyp.r2_score and best_hyp.r2_score > self._LLM_ACCEPT_R2:
and change
    if best_hyp.r2_score is None or best_hyp.r2_score < 0.5:
to  if (not self._LLM_PRIOR_SEED) or best_hyp.r2_score is None or best_hyp.r2_score < 0.5:
"""

_mods = {}


def _load():
    if not _mods:
        import importlib
        exp1 = importlib.import_module(EXP1_MODULE)
        eng = importlib.import_module(ENGINE_MODULE)
        cls = eng.SymbolicEngineWithLLM
        for _, sw in GATE_SWITCHES.items():
            if sw and not hasattr(cls, sw[0]):
                raise RuntimeError(f"engine lacks {sw[0]}: apply ENGINE_PATCH first\n{ENGINE_PATCH}")
        _mods["exp1"], _mods["eng"] = exp1, eng   # cache only after the check passes
    return _mods["exp1"], _mods["eng"].SymbolicEngineWithLLM


@contextlib.contextmanager
def _gates_off(cls, disabled):
    saved = {}
    try:
        for c in disabled:
            attr, val = GATE_SWITCHES[c]
            saved[attr] = getattr(cls, attr)
            setattr(cls, attr, val)
        yield
    finally:
        for attr, val in saved.items():
            setattr(cls, attr, val)


def _sha(*arrays):
    # TODO(hash scheme): must equal run_pure_llm_arm.py's train_data_sha256 / far_data_sha256
    # or G1 against the P arm will fail.  Check how it hashes (dtype, order, which arrays).
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(np.asarray(a, dtype=float)).tobytes())
    return h.hexdigest()


def _rescore_far(res):
    # TODO(r2_checked): score the discovered formula on the far data through
    # hypatiax.core.r2_canonical.r2_checked (needs formula + x_log_flags/y_log, which
    # run_condition does not return).  Until then this reuses run_condition's _safe_r2.
    if os.environ.get("P3_ALLOW_SAFE_R2") != "1":
        raise NotImplementedError(
            "rescore through r2_checked is not wired; set P3_ALLOW_SAFE_R2=1 for a smoke test only")
    return res.get("extrap_r2_far")


_MODEL_ID = []


def _model_id():
    if _MODEL_ID:
        return _MODEL_ID[0]
    _MODEL_ID.append(_model_id_uncached())
    return _MODEL_ID[0]


def _model_id_uncached():
    # TODO(model_id): read the real model string from the LLM config actually used.
    try:
        from hypatiax.tools.symbolic.symbolic_engine import LLMConfig
        return str(getattr(LLMConfig(enabled=True), "model", "unknown"))
    except Exception:
        return "unknown"


def _prompt_sha():
    # TODO(prompt hash): hash the prompt template the engine uses (same value as the P arm's
    # prompt_template_sha256 only if the prompts are shared; G4 wants ONE hash across rows).
    return "unknown"


def _preflight():
    """Fail BEFORE spending compute on a row that cannot be valid."""
    if os.environ.get("P3_ALLOW_SAFE_R2") != "1":
        raise NotImplementedError(
            "rescore through r2_checked is not wired; set P3_ALLOW_SAFE_R2=1 for a smoke test only")
    if os.environ.get("P3_ALLOW_UNKNOWN_META") != "1" and (
            _model_id() == "unknown" or _prompt_sha() == "unknown"):
        raise RuntimeError(
            "model_id / prompt_template_sha256 are 'unknown' (would trivially pass G4); "
            "wire them, or set P3_ALLOW_UNKNOWN_META=1 for a smoke test only")


@contextlib.contextmanager
def _rng_isolated():
    """Data generation for hashing must not perturb the RNG stream run_condition sees."""
    import random
    np_state, py_state = np.random.get_state(), random.getstate()
    try:
        yield
    finally:
        np.random.set_state(np_state)
        random.setstate(py_state)


def run_case(equation, seed, disabled, timeout_s):
    unmapped = [c for c in disabled if GATE_SWITCHES.get(c) is None]
    if unmapped:
        raise NotImplementedError(
            f"no engine switch mapped for {unmapped}: run only llm_acceptance,pysr_prior "
            "and --omit the rest in phase3_close.py")
    _preflight()
    exp1, cls = _load()
    eq = next(e for e in exp1.CORE_15 if e["name"] == equation)
    eq_seed = seed + exp1.EQ_ID.get(equation, 0) * 7

    # TODO(hash provenance): N, noise_level, eq_seed and the 6-tuple unpack are guesses at what
    # run_condition does internally; verify, or hash the arrays run_condition actually used.
    with _rng_isolated():
        X_tr, _, y_tr, _, _, _ = exp1.generate_data(eq, N=200, noise_level=0.05, seed=eq_seed)
        X_far, y_far = exp1.generate_extrap_data(eq, regime="far", N=100, seed=eq_seed)

    with _gates_off(cls, disabled):
        res = exp1.run_condition(eq, "hypatia", seed=seed, wall_clock_limit=timeout_s)

    timed_out = bool(res.get("timed_out"))
    r2 = None if timed_out else _rescore_far(res)
    finite = r2 is not None and math.isfinite(float(r2))
    llm_called = bool(res.get("llm_called", False))
    if timed_out:
        status = "timeout"
    elif not res.get("success", False) or not finite:
        status = "failed"
    else:
        status = "ok"

    # Control check: the gate must have changed behaviour, else the row is not an ablation.
    if "llm_acceptance" in disabled and res.get("llm_mode_used") == "hybrid_llm_only":
        raise RuntimeError("llm_acceptance ablated but the LLM-only shortcut still fired")

    return {
        "status": status,
        "r2_raw": float(r2) if finite else float("-inf"),
        "formula": res.get("best_expression"),
        "generation_path": "symbolic+llm" if llm_called else "symbolic",
        "llm_called": llm_called,
        "bypass_used": res.get("bypass_kind", "none") not in ("none", None),
        "model_id": _model_id(),
        "train_data_sha256": _sha(X_tr, y_tr),
        "far_data_sha256": _sha(X_far, y_far),
        "prompt_template_sha256": _prompt_sha(),
        "extrap_r2_far": res.get("extrap_r2_far"),
        "timed_out": timed_out,
        "error_stage": res.get("error"),
    }
