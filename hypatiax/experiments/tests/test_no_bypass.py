# hypatiax/experiments/tests/test_no_bypass.py
import os, pathlib, re
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-offline")
from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import PureLLMBaseline

CASES = [("Gaussian/normal distribution probability density", ["theta", "sigma"]),
         ("Planck blackbody spectral radiance (dimensionless)", ["x"]),
         ("Bose-Einstein occupation number for bosons", ["f", "T"]),
         ("Nernst equation for electrode potential", ["T", "ox", "red"]),
         ("Michaelis-Menten enzyme kinetics", ["S"])]

def test_hardcoded_formula_is_noop(monkeypatch):
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    monkeypatch.setenv("HYPATIAX_DISABLE_HARDCODED", "0")
    b = PureLLMBaseline()
    for d, v in CASES:
        assert b._try_hardcoded_formula(d, d.lower(), v, {}) is None

def test_no_bypass_fingerprints():
    src = pathlib.Path("hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py").read_text()
    for s in ("pure_llm_hardcoded", "exact formula bypass", "_make_formula_dict", "_ols_"):
        assert s not in src, s
