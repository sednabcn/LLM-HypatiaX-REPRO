"""Regression tests for baseline_pure_llm_defi_discovery.py (run: pytest -q)."""
import importlib, os, sys, types
import numpy as np
import pytest
from pathlib import Path

# locate the module wherever it lives in the repo
_here = Path(__file__).resolve()
for _root in (_here.parent, *_here.parents):
    _hits = [h for h in _root.rglob("baseline_pure_llm_defi_discovery.py") if "site-packages" not in h.parts]
    if _hits:
        sys.path.insert(0, str(_hits[0].parent))
        break

@pytest.fixture()
def mod(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    for k in ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS", "HYPATIAX_ALLOW_LEGACY"):
        monkeypatch.delenv(k, raising=False)
    stub = types.ModuleType("hypatiax.protocols.experiment_protocol_defi")
    stub.DeFiExperimentProtocol = object
    for n in ("hypatiax", "hypatiax.protocols"):
        sys.modules.setdefault(n, types.ModuleType(n))
    sys.modules["hypatiax.protocols.experiment_protocol_defi"] = stub
    sys.modules.pop("baseline_pure_llm_defi_discovery", None)
    return importlib.import_module("baseline_pure_llm_defi_discovery")

def test_flags_fail_closed(mod):
    assert mod._flag("HYPATIAX_DISABLE_HARDCODED") and mod._flag("HYPATIAX_DISABLE_PROMPT_HINTS")

def test_legacy_requires_explicit_optin(mod, monkeypatch):
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    assert not mod._flag("HYPATIAX_DISABLE_PROMPT_HINTS")

def test_explicit_zero_without_optin_still_reported_off(mod, monkeypatch):
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", "0")
    assert not mod._flag("HYPATIAX_DISABLE_PROMPT_HINTS")  # run_all.sh forces it back to 1

@pytest.mark.parametrize("desc", ["Gaussian probability density", "Fourier heat conduction",
                                  "Nernst electrode potential", "Clausius dielectric effective field"])
def test_no_ground_truth_in_prompt_when_hints_disabled(mod, desc):
    p = mod.PureLLMBaseline()._generate_standard_prompt(desc, "d", ["x", "mu", "sigma"], {})
    assert "sqrt(2*pi)" not in p and "MANDATORY" not in p and "FORMULA HINT" not in p

def _r2(mod, y, pred):
    return mod.PureLLMBaseline().test_formula_accuracy(
        {"python_code": "def formula(x):\n    return x"}, pred.reshape(-1, 1), y, ["x"])

def test_large_offset_nonconstant_target_not_scored_perfect(mod):
    rng = np.random.default_rng(0)
    y = 1e6 + rng.normal(0, 1, 200)
    r = _r2(mod, y, y + rng.normal(0, 5, 200))
    assert r["r2"] < 0

def test_tiny_scale_targets_still_scored(mod):
    rng = np.random.default_rng(1)
    y = 1e-19 * rng.uniform(1, 2, 100)
    assert _r2(mod, y, y)["r2"] == pytest.approx(1.0)

def test_constant_target_exact_match_is_one_mismatch_is_neg_inf(mod):
    y = np.full(50, 3.0)
    assert _r2(mod, y, y.copy())["r2"] == 1.0
    assert _r2(mod, y, y + 0.1)["r2"] == float("-inf")


# ───────────── provenance / model / JSON fixes ─────────────
class _Boom:
    class messages:  # noqa: N801
        @staticmethod
        def create(**kw):
            raise RuntimeError("api rejected")


class _Capture:
    """Stub client that records the prompt it is asked to send, then fails."""
    def __init__(self):
        self.prompts = []
        outer = self

        class messages:  # noqa: N801
            @staticmethod
            def create(**kw):
                outer.prompts.append(str(kw.get("messages")))
                raise RuntimeError("api rejected")

        self.messages = messages


FORBIDDEN = ("MANDATORY", "CODE TEMPLATE", "NEVER use", "FORMULA HINT",
             "E0 - (R*T", "np.log(c_ox", "n_elec=2", "sqrt(2*pi)")


def test_error_row_is_not_counted_as_llm_call_even_in_legacy_mode(mod, monkeypatch):
    # Legacy mode can no longer embed ground truth: the hint code was deleted.
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    b = mod.PureLLMBaseline(); b.client = _Capture()
    r = b.generate_formula("Liquidation price for leveraged long", "defi",
                           ["entry_price", "leverage"], {})
    assert r["llm_attempted"] is True and r["llm_called"] is False
    assert r["error_stage"] == "api_request"
    assert r["bypass_kind"] == "live"
    assert r["prompt_sha256"] and r["temperature_sent"] is False
    assert b.client.prompts, "prompt was never built"
    assert not any(s in b.client.prompts[0] for s in FORBIDDEN)


def test_clean_run_error_row_is_live(mod):
    b = mod.PureLLMBaseline(); b.client = _Boom()
    r = b.generate_formula("Liquidation price", "defi", ["p", "l"], {})
    assert r["bypass_kind"] == "live" and r["bypass_flags"]["disable_prompt_hints"] is True


def test_constants_recorded_in_provenance(mod):
    b = mod.PureLLMBaseline(); b.client = _Boom()
    r = b.generate_formula("Nernst", "chem", ["a", "b"], {"constants": {"R": 8.314}})
    assert r["prompt_constants"] == {"R": 8.314}


def test_model_resolution_precedence(mod, monkeypatch, tmp_path):
    cfg = tmp_path / "repro.yaml"; cfg.write_text('llm_model: "from-yaml"\n')
    monkeypatch.setenv("REPRO_CFG", str(cfg))
    assert mod.resolve_model() == ("from-yaml", f"repro.yaml:{cfg}")
    monkeypatch.setenv("HYPATIAX_LLM_MODEL", "from-env")
    assert mod.resolve_model()[0] == "from-env"
    assert mod.resolve_model("explicit")[0] == "explicit"


def test_results_json_is_strict(mod, tmp_path):
    import json
    b = mod.PureLLMBaseline()
    b.results.append({"evaluation": {"r2": float("-inf"), "x": float("nan")}})
    f = tmp_path / "out" / "r.json"
    b.save_results(str(f))
    data = json.loads(f.read_text(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    assert data[0]["evaluation"]["r2"] is None


def test_r2_status_reported(mod):
    y = np.full(20, 2.0)
    assert _r2(mod, y, y + 1)["r2_status"] == "constant_target_mismatch"
    assert _r2(mod, y, y.copy())["r2_status"] == "constant_target_match"
