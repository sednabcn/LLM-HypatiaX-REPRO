"""Prompt-capture regression test: the Pure LLM baseline must never send
equation-specific hints. Run: pytest test_no_equation_hints.py
Set BASELINE_PATH=/path/to/file.py to test a specific copy; otherwise it is
found under hypatiax/core/base_pure_llm/ or next to this file."""
import importlib, importlib.util, os, pathlib, sys, types
import pytest

FORBIDDEN = (
    "MANDATORY", "CODE TEMPLATE", "FORMULA HINT", "NEVER use", "DO NOT use (epsilon",
    "E0 - (R*T", "np.log(c_ox", "n_elec=2", "(epsilon - 1) / (epsilon + 2)",
    "kappa * (T2 - T1) / d", "1 / (sigma * np.sqrt", "1/(sigma*sqrt(2*pi))",
    "CRITICAL: Use EXACT formula", "ESTIMATED PARAMETERS", "maintenance_margin",
    "Kleiber", "0.75",
)
TASKS = [
    ("Nernst equation electrode potential", ["E0", "T", "c_ox"], {"constants": {"R": 8.314, "F": 96485}}),
    ("Clausius-Mossotti local effective field", ["epsilon", "E_external"], {}),
    ("Fourier heat conduction flux", ["kappa", "T1", "T2", "d"], {}),
    ("Gaussian probability density", ["x", "mu", "sigma"], {}),
    ("Liquidation price for long position", ["entry_price", "leverage"], {}),
    ("Optimal Kelly fraction for LP position", ["expected_fee_apy", "il_risk"], {}),
    ("Logistic growth rate", ["N"], {}),
    ("Michaelis-Menten enzyme kinetics", ["S"], {}),
    ("Arrhenius rate constant", ["T"], {}),
]

class _Msg:
    def __init__(self): self.content = [types.SimpleNamespace(type="text", text="FORMULA:\nx\nPYTHON:\ndef formula(x):\n    return x")]; self.stop_reason="end_turn"; self.usage=None

class _Client:
    def __init__(self): self.sent = []
    @property
    def messages(self): return self
    def create(self, **kw): self.sent.append(kw["messages"][0]["content"]); return _Msg()

def _find_baseline_path():
    """BASELINE_PATH env wins; else search the repo layout, then next to this file."""
    env = os.environ.get("BASELINE_PATH")
    if env:
        return pathlib.Path(env).resolve()
    here = pathlib.Path(__file__).resolve().parent
    rel = pathlib.Path("hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py")
    for base in (here, *here.parents):
        for cand in (base / rel, base / "baseline_pure_llm_defi_discovery.py"):
            if cand.is_file():
                return cand
    raise FileNotFoundError("set BASELINE_PATH=/path/to/baseline_pure_llm_defi_discovery.py")


def _stub_if_missing(name, attrs):
    """Use the real package when installed; stub only on ImportError."""
    try:
        importlib.import_module(name)
    except Exception:
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m


@pytest.fixture
def baseline(monkeypatch):
    _stub_if_missing("anthropic", {"Anthropic": lambda **k: _Client()})
    _stub_if_missing("dotenv", {"load_dotenv": lambda **k: None})
    _stub_if_missing("hypatiax", {})
    _stub_if_missing("hypatiax.protocols", {})
    _stub_if_missing("hypatiax.protocols.experiment_protocol_defi", {"DeFiExperimentProtocol": object})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    path = _find_baseline_path()
    spec = importlib.util.spec_from_file_location("_baseline_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    b = mod.PureLLMBaseline()
    b.client = _Client()          # never touch the network
    b._path = str(path)
    return b

@pytest.mark.parametrize("flags", [("1", "1"), ("0", "0")])
@pytest.mark.parametrize("desc,vars_,meta", TASKS)
def test_no_equation_specific_hints(baseline, monkeypatch, flags, desc, vars_, meta):
    monkeypatch.setenv("HYPATIAX_DISABLE_HARDCODED", flags[0])
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", flags[1])
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    import numpy as np
    X = np.linspace(1, 10, 20).reshape(-1, 1); y = X[:, 0] ** 2
    row = baseline.generate_formula(desc, "test", vars_, dict(meta), X=X, y=y)
    sent = baseline.client.sent[-1]
    hits = [s for s in FORBIDDEN if s in sent]
    assert not hits, f"leak markers in prompt: {hits}"
    assert row["bypass_kind"] == "live"

def test_prompt_identical_across_flag_values(baseline, monkeypatch):
    """The flags must not change the prompt at all (nothing left to gate)."""
    shas = set()
    for f in ("0", "1"):
        monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", f)
        monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
        shas.add(baseline.generate_formula("Nernst equation electrode potential", "t", ["E0","T"], {})["prompt_sha256"])
    assert len(shas) == 1
