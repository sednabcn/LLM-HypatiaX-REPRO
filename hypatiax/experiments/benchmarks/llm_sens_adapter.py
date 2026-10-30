"""
llm_sens_adapter.py -- runner for exp1_llm_sens / ablation_conditions.py.

    runner = llm_sens_adapter:run      (put this file in hypatiax/experiments/benchmarks/)

Arms
  pysr_only, hypatia, hypatia_nollm : exp1_ablation.run_condition(eq, arm, seed)
  pure_llm                          : hypatia.get_llm_prior -> best candidate by train R2
                                      (no PySR, no constant fitting)

The protocol's own arrays replace exp1_ablation's data generator for the call
(monkeypatching exp1_ablation.generate_data / generate_extrap_data), so the benchmark
keeps its small noisy training set and its clean extrapolated test set.
Every extrapolation regime name (near/medium/far) therefore maps to the SAME test set.

Never put ground truth into eq: it stays in eq["fn"] (evaluator side) and is not a
prompt field. Neutral cases carry names x0.. and a generic description.
"""
from __future__ import annotations

import contextlib
import importlib
import json
import math
import os
import re
import traceback

import numpy as np

DOMAIN_SLUG = os.environ.get("LLM_SENS_DOMAIN_SLUG", "defi_amm")   # see note in README / reply


def _protocol_funcs(n):
    try:
        mod = importlib.import_module("hypatiax.protocols.experiment_protocol_defi_llm_sensitive")
    except ModuleNotFoundError:
        mod = importlib.import_module("experiment_protocol_defi_llm_sensitive")
    proto = mod.DeFiLLMSensitiveProtocol()
    for d in proto.get_all_domains():      # deterministic: repopulates mod.FUNCS
        proto.load_test_data(d, n)
    return mod.FUNCS


def _r2(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    if not np.all(np.isfinite(p)):
        return None
    ss = float(np.sum((y - y.mean()) ** 2))
    return None if ss == 0 else float(1 - np.sum((y - p) ** 2) / ss)


def _build_eq(case, cid, truth, funcs, neutral):
    desc, X, y, names, meta = case
    s = meta["split_index"]
    ranges = [tuple(r) for r in meta["train_ranges"]]
    ext = meta.get("test_range_extrapolated_var")
    ext_ranges = list(ranges)
    if ext:
        ext_ranges[names.index(ext["var"])] = tuple(ext["range"])
    return {
        "id": cid.replace(":", "_"),
        "name": "unknown function" if neutral else desc,
        "vars": list(names),
        "domain": DOMAIN_SLUG,
        "formula_hint": "" if neutral else desc,     # description only, never the formula
        "train_range": ranges,
        "extrap_range": ext_ranges,
        "fn": funcs[truth],                           # evaluator-side true function
        "formula_sympy": None,
    }, (X[:s], y[:s], X[s:], y[s:])


@contextlib.contextmanager
def _data_override(m, Xtr, ytr, Xte, yte):
    og, oe = m.generate_data, m.generate_extrap_data
    Xall, yall = np.vstack([Xtr, Xte]), np.concatenate([ytr, yte])
    m.generate_data = lambda eq, N=200, noise_level=0.05, seed=42: (Xtr, Xte, ytr, yte, Xall, yall)
    m.generate_extrap_data = lambda eq, regime="medium", N=100, seed=42: (Xte, yte)
    try:
        yield
    finally:
        m.generate_data, m.generate_extrap_data = og, oe


_NS = {k: getattr(np, k) for k in
       ("sqrt", "exp", "log", "sin", "cos", "tan", "abs", "tanh", "arctan", "power")}
_NS.update(np=np, math=math, pi=math.pi, e=math.e)


def _pure_llm(eq, Xtr, ytr, Xte, yte):
    import hypatia   # attribute patched by ablation_conditions (cache_salt, blind)
    exprs = hypatia.get_llm_prior(eq, Xtr, ytr, n_candidates=5, verbose=False)
    best = None
    for ex in exprs or []:
        try:
            ns = dict(_NS, **{v: Xtr[:, i] for i, v in enumerate(eq["vars"])})
            tr = _r2(ytr, eval(ex, {"__builtins__": {}}, ns))   # noqa: S307  (restricted namespace)
            if tr is not None and (best is None or tr > best[0]):
                best = (tr, ex)
        except Exception:
            continue
    out = {"condition": "pure_llm", "llm_called": True, "n_candidates": len(exprs or [])}
    if best is None:
        return dict(out, error="no valid candidate expression", train_r2=None, extrap_r2=None)
    ns = dict(_NS, **{v: Xte[:, i] for i, v in enumerate(eq["vars"])})
    try:
        te = _r2(yte, eval(best[1], {"__builtins__": {}}, ns))   # noqa: S307
    except Exception:
        te = None
    return dict(out, error=None, best_expr=best[1], train_r2=best[0], extrap_r2=te)


def run(cases, case_ids, arm, seed, condition, out_dir):
    truth = json.load(open(os.environ["LLM_SENS_TRUTH"]))
    funcs = _protocol_funcs(len(cases[0][1]))
    neutral = condition["description"] == "neutral"
    m = None if arm == "pure_llm" else importlib.import_module("exp1_ablation")
    results = {}
    for cid, case in zip(case_ids, cases):
        eq, (Xtr, ytr, Xte, yte) = _build_eq(case, cid, truth[cid], funcs, neutral)
        try:
            if arm == "pure_llm":
                res = _pure_llm(eq, Xtr, ytr, Xte, yte)
            else:
                with _data_override(m, Xtr, ytr, Xte, yte):
                    res = m.run_condition(eq, arm, seed=seed)
        except Exception as exc:               # a failure is a failure, not a score
            traceback.print_exc()
            res = {"condition": arm, "error": f"{type(exc).__name__}: {exc}", "failed": True}
        results[cid] = {"stratum": case[4].get("stratum", case[4].get("domain")),
                        "description_condition": condition["description"], "result": res}
    return results
