"""Regression tests for the Pure LLM baseline (release hardening).

1. The prompt sent to the API contains no equation-specific hint, template,
   data-derived parameter or target-law text, whatever the flags say.
2. Prompts for different tasks are identical once the task description is
   masked (input parity: only the task itself differs).
3. R^2 follows the canonical policy (degenerate target, tiny scale, non-finite
   prediction, sign-flip off by default and recorded).

Offline: the API call is replaced by a capture stub. No key or network needed.
"""
import types

import numpy as np
import pytest

from hypatiax.core.base_pure_llm import baseline_pure_llm_defi_discovery as B

DESCRIPTIONS = [
    "Nernst equation electrode potential",
    "Clausius-Mossotti local effective field in a dielectric",
    "Fourier heat conduction heat flux through a slab",
    "Gaussian probability density function",
    "Optimal Kelly fraction for an LP position",
    "Liquidation price for a long leveraged position",
    "Maximum leverage given acceptable loss",
    "Required collateral for leveraged position",
    "Logistic growth rate of a population",
    "Michaelis-Menten enzyme kinetics",
    "Allometric scaling of metabolic rate with mass",
    "Arrhenius rate constant",
    "Some neutral task description",
]
FORBIDDEN = [
    "MANDATORY", "CODE TEMPLATE", "FORMULA HINT", "NEVER use", "DO NOT use (", "DO NOT include an area",
    "CRITICAL:", "CRITICAL RULES", "ESTIMATED PARAMETERS", "EXACT formula",
    "np.log(c_ox", "n_elec", "(epsilon - 1)", "kappa * (T2 - T1)",
    "1/(sigma*sqrt(2*pi))", "1 / (sigma * np.sqrt", "normalization constant",
    "Kleiber", "carrying capacity", "maintenance_margin", "* 0.8",
]
FLAG_SETTINGS = [
    {},  # unset
    {"HYPATIAX_DISABLE_HARDCODED": "1", "HYPATIAX_DISABLE_PROMPT_HINTS": "1"},
    {"HYPATIAX_DISABLE_HARDCODED": "0", "HYPATIAX_DISABLE_PROMPT_HINTS": "0",
     "HYPATIAX_ALLOW_LEGACY": "1"},   # legacy opt-in must not bring any hint back
]
FLAG_ENV = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS",
            "HYPATIAX_ALLOW_LEGACY", "HYPATIAX_R2_SIGN_FLIP")


@pytest.fixture
def baseline(monkeypatch):
    for k in FLAG_ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured = []

    def fake_create(client, **kwargs):
        captured.append(kwargs["messages"][0]["content"])
        block = types.SimpleNamespace(
            type="text", text="FORMULA:\nx\n\nPYTHON:\ndef formula(x):\n    return x\n")
        return types.SimpleNamespace(content=[block], stop_reason="end_turn",
                                     usage=types.SimpleNamespace(input_tokens=1, output_tokens=1))

    monkeypatch.setattr(B, "_create_message", fake_create)
    b = B.PureLLMBaseline()
    b._captured = captured
    return b


def _prompt(b, monkeypatch, desc, flags):
    for k in FLAG_ENV:
        monkeypatch.delenv(k, raising=False)
    for k, v in flags.items():
        monkeypatch.setenv(k, v)
    rng = np.random.default_rng(0)
    X, y = rng.uniform(1, 2, (30, 2)), rng.uniform(1, 2, 30)
    row = b.generate_formula(desc, "test_domain", ["x0", "x1"],
                             {"constants": {"R": 8.314}}, X=X, y=y)
    assert row["llm_called"] is True and row["bypass_kind"] == "live", row.get("error")
    assert row["specialized_prompt"] is False
    return b._captured[-1]


@pytest.mark.parametrize("flags", FLAG_SETTINGS)
@pytest.mark.parametrize("desc", DESCRIPTIONS)
def test_prompt_has_no_leaked_hints(baseline, monkeypatch, desc, flags):
    p = _prompt(baseline, monkeypatch, desc, flags)
    leaked = [s for s in FORBIDDEN if s in p]
    assert not leaked, f"leaked text in prompt for {desc!r}: {leaked}"


def test_prompts_identical_except_description(baseline, monkeypatch):
    masked = {_prompt(baseline, monkeypatch, d, {}).replace(d, "<TASK>") for d in DESCRIPTIONS}
    assert len(masked) == 1, "prompt differs between tasks beyond the task description"


def test_prompt_independent_of_flags(baseline, monkeypatch):
    for d in DESCRIPTIONS:
        seen = {_prompt(baseline, monkeypatch, d, f) for f in FLAG_SETTINGS}
        assert len(seen) == 1, f"flags change the prompt for {d!r}"


# ----------------------------------------------------------------- R^2 policy
def _score(b, code, x, y):
    return b.test_formula_accuracy({"python_code": code}, np.asarray(x).reshape(-1, 1), y, ["x"])


def test_constant_target_is_degenerate_not_perfect(baseline):
    x = np.linspace(1, 2, 20)
    r = _score(baseline, "def formula(x):\n    return x*0+3.0", x, np.full(20, 3.0))
    assert r["success"] is False and r["r2_status"] == "degenerate_target" and np.isnan(r["r2"])


def test_large_offset_small_spread_is_scored_not_constant(baseline):
    rng = np.random.default_rng(1)
    x = np.linspace(1, 2, 200)
    y = 1e6 + rng.normal(0, 1, 200)
    r = _score(baseline, "def formula(x):\n    return x*0+1e6", x, y)
    assert r["r2_status"] == "ok" and r["r2"] < 0.5          # not 1.0


def test_tiny_scale_target_is_scored(baseline):
    x = np.linspace(1, 2, 50)
    y = 1e-19 * x
    r = _score(baseline, "def formula(x):\n    return 1e-19*x", x, y)
    assert r["success"] and r["r2_status"] == "ok" and r["r2"] == pytest.approx(1.0)


def test_nonfinite_prediction_is_failure(baseline):
    x = np.linspace(1, 2, 20)
    r = _score(baseline, "def formula(x):\n    return x*float('nan')", x, x)
    assert r["success"] is False and r["r2"] == float("-inf") and r["r2_status"] == "nonfinite_pred"


def test_sign_flip_off_by_default_and_recorded(baseline, monkeypatch):
    x = np.linspace(1, 2, 50)
    r = _score(baseline, "def formula(x):\n    return -x", x, x)
    assert r["r2_sign_flip"] is False and r["r2"] < 0
    monkeypatch.setenv("HYPATIAX_R2_SIGN_FLIP", "1")
    r2 = _score(baseline, "def formula(x):\n    return -x", x, x)
    assert r2["r2_sign_flip"] is True and r2["r2"] == pytest.approx(1.0)
