#!/usr/bin/env python3
"""Offline audit: which protocol tasks are intercepted by PureLLMBaseline hardcoded/OLS paths?
No LLM calls. Calls _try_hardcoded_formula with HYPATIAX_DISABLE_HARDCODED off, then on.
Run from the repo root:  python bypass_audit.py"""
import os, sys, json, csv
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-offline")   # client is built but never called
sys.path.insert(0, os.getcwd())
import numpy as np
from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import PureLLMBaseline as B

b = B()
def probe(desc, domain, vnames, meta, X=None, y=None):
    """Mirror generate_formula's OLS enrichment, then call the bypass directly."""
    meta = dict(meta or {})
    out = {}
    for flag in ("0", "1"):
        os.environ["HYPATIAX_DISABLE_HARDCODED"] = flag
        r = None
        try:
            r = b._try_hardcoded_formula(desc, desc.lower(), list(vnames), meta)
        except Exception as e:
            r = {"_err": repr(e)[:80]}
        out[flag] = r
    os.environ.pop("HYPATIAX_DISABLE_HARDCODED", None)
    on = out["0"]
    return (on is not None and "_err" not in (on or {})), out["1"] is None, (on or {})

rows = []
# Feynman suite
from hypatiax.protocols.experiment_protocol_benchmark_v2 import _build_feynman_equations
for eq in _build_feynman_equations():
    d, X, y, vn, meta = eq.generate(num_samples=200, noise_level=0.0, seed=42)
    hit, off_clean, r = probe(d, eq.domain, vn, meta, X, y)
    rows.append(("feynman", eq.feynman_id, d, hit, off_clean, r.get("method", "")))
# DeFi suite
from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
P = DeFiExperimentProtocol()
for dom in P.get_all_domains():
    for t in P.load_test_data(dom, 100):
        d, X, y, vn, meta = t[0], t[1], t[2], t[3], (t[4] if len(t) > 4 else {})
        hit, off_clean, r = probe(d, dom, vn, meta, X, y)
        rows.append(("defi", dom, d, hit, off_clean, r.get("method", "")))

with open("bypass_audit.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["suite","id_or_domain","description","bypassed_when_switch_off","switch_on_returns_None","method"]); w.writerows(rows)
for s in ("feynman", "defi"):
    sub = [r for r in rows if r[0] == s]
    print(s, "tasks:", len(sub), "bypassed:", sum(r[3] for r in sub), "switch restores LLM path for all bypassed:", all(r[4] for r in sub if r[3]))
print("\nBypassed tasks:")
for r in rows:
    if r[3]: print(f"  [{r[0]}] {r[1]:<12} {r[2][:70]}  ({r[5]})")
