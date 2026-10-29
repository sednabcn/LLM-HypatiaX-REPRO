"""Prompt leak + parity test: Pure-LLM baseline vs the nn hybrid's local fallback.

Run:  pytest test_prompt_parity.py -q -s      (-s prints the cross-system diffs)

Checks, per task and per system:
  1. No equation-specific text (named templates, formulas, solved constants).
  2. No pre-solved answer shape: a pre-filled FORMULA line or a `return <expr>` body.
  3. Information parity: description, variable names and constants are present.
  4. No decimal / multi-digit numbers in the scaffold beyond what the task supplies.

TASKS covers every keyword the old hint / hardcoded branches dispatched on, so a pass
means those branches no longer reach the prompt. Replace the placeholder descriptions
with the exact strings from the protocol files.
"""
import difflib
import re
from dataclasses import dataclass, field

import pytest

FORBIDDEN = (
    "MANDATORY", "CODE TEMPLATE", "NEVER use", "FORMULA HINT",
    "DO NOT include an area", "DO NOT use (epsilon",
    # Nernst
    "E0 - (R*T", "np.log(c_ox", "n_elec=2",
    # Fourier
    "kappa * (T2", "delta_T / d",
    # Gaussian
    "1/(sigma", "sqrt(2*pi)",
    # Clausius-Mossotti
    "(epsilon - 1", "(epsilon + 2",
    # impermanent loss / VaR / ES / Kelly (old pre-solved answers)
    "2*sqrt(r)/(1+r)", "2.0 * np.sqrt(r)", "1.6449", "1.254",
    "risk_aversion = 2.0", "mu / (lambda",
)

# Generic detectors for a pre-solved answer embedded in the prompt.
PREFILLED_FORMULA = re.compile(r"FORMULA:\s*\n\s*(?!\[)\S")
SOLVED_RETURN = re.compile(r"^[ \t]+return[ \t]+(?!result\b|\.\.\.)\S", re.MULTILINE)  # code lines only


@dataclass(frozen=True)
class Task:
    id: str
    description: str
    domain: str
    variables: tuple
    constants: dict = field(default_factory=dict)

    @property
    def metadata(self):
        return {"constants": dict(self.constants)} if self.constants else {}


TASKS = [
    Task("nernst", "Nernst equation for electrode potential", "electrochemistry",
         ("E0", "T", "c_ox", "c_red"), {"R": 8.314, "F": 96485}),
    Task("fourier", "Fourier law of heat conduction: heat flux through a slab",
         "thermodynamics", ("kappa", "T2", "T1", "d")),
    Task("gaussian", "Gaussian probability density", "statistics", ("x", "mu", "sigma")),
    Task("kelly", "Optimal Kelly fraction for LP position sizing", "defi", ("mu", "sigma")),
    Task("impermanent_loss", "Impermanent loss for a constant-product pool", "defi", ("r",)),
    # --- remaining keywords the old branches dispatched on ---
    Task("liquidation_long", "Liquidation price for leveraged long", "defi",
         ("entry_price", "leverage")),
    Task("liquidation_short", "Liquidation price for leveraged short", "defi",
         ("entry_price", "leverage")),
    Task("max_leverage", "Maximum leverage given the collateral ratio", "defi",
         ("collateral_ratio",)),
    Task("collateral", "Required collateral for leveraged position", "defi",
         ("position_size", "leverage")),
    Task("capital_efficiency", "Capital efficiency of concentrated liquidity", "defi",
         ("price", "p_low", "p_high")),
    Task("portfolio_es", "Portfolio expected shortfall for correlated assets", "defi",
         ("w1", "w2", "sigma1", "sigma2", "rho")),
    Task("logistic", "Logistic growth rate", "biology", ("N", "r", "K")),
    Task("michaelis_menten", "Michaelis-Menten reaction rate", "biology", ("S", "Vmax", "Km")),
    Task("allometric", "Allometric scaling of metabolic rate with body mass", "biology", ("M",)),
    Task("arrhenius", "Arrhenius rate constant", "chemistry", ("T", "Ea", "A"), {"R": 8.314}),
    Task("clausius", "Clausius-Mossotti local effective field in a dielectric",
         "electromagnetism", ("epsilon", "E_ext")),
]


class _Stop(Exception):
    pass


class _RecordingClient:
    """Stands in for anthropic.Anthropic: records the request, then aborts."""

    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        raise _Stop("captured")


@pytest.fixture(autouse=True)
def clean_run_env(monkeypatch):
    monkeypatch.setenv("HYPATIAX_DISABLE_HARDCODED", "1")
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", "1")
    monkeypatch.setenv("HYPATIAX_R2_SIGN_FLIP", "0")
    monkeypatch.delenv("HYPATIAX_ALLOW_LEGACY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def _baseline_prompt(task, monkeypatch):
    from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import PureLLMBaseline

    b = PureLLMBaseline()
    rec = _RecordingClient()
    b.client = rec
    b.generate_formula(task.description, task.domain, list(task.variables), task.metadata)
    assert rec.calls, (
        "no API call captured for the baseline: a hardcoded/cache path answered "
        "before the LLM was reached (that is itself a finding)"
    )
    return rec.calls[0]["messages"][0]["content"]


def _hybrid_prompt(task, monkeypatch):
    from hypatiax.core.generation.hybrid_defi_system.hybrid_system_nn_defi_domain import (
        EnhancedHybridSystemDeFi,
    )

    # _standard_prompt does not use self, so no constructor / API client is needed.
    return EnhancedHybridSystemDeFi._standard_prompt(
        None, task.description, task.domain, list(task.variables), task.metadata
    )


def _all_domains_prompt(task, monkeypatch):
    import inspect

    import hypatiax.core.generation.hybrid_all_domains_llm_nn.hybrid_system_llm_nn_all_domains as m

    owners = [c for c in vars(m).values()
              if inspect.isclass(c) and "_generate_prompt" in c.__dict__]
    assert len(owners) == 1, f"expected one class defining _generate_prompt, found {owners}"
    # _generate_prompt reads only module-level helpers, so no constructor / client is needed.
    return owners[0]._generate_prompt(
        None, task.description, task.domain, list(task.variables), task.metadata
    )


SYSTEMS = {
    "baseline": _baseline_prompt,
    "hybrid_local_fallback": _hybrid_prompt,
    "hybrid_all_domains_fallback": _all_domains_prompt,
}


def _scaffold(prompt, task):
    """Prompt with the task-supplied text removed, leaving each system's own scaffolding."""
    s = prompt.replace(task.description, " ")
    for tok in (*task.variables, *map(str, task.constants), *map(str, task.constants.values())):
        s = re.sub(rf"(?<!\w){re.escape(tok)}(?!\w)", " ", s)
    return s


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
@pytest.mark.parametrize("system", list(SYSTEMS))
def test_no_equation_specific_text(system, task, monkeypatch):
    prompt = SYSTEMS[system](task, monkeypatch)
    hits = [s for s in FORBIDDEN if s in prompt]
    assert not hits, f"{system}/{task.id}: forbidden text in prompt: {hits}"


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
@pytest.mark.parametrize("system", list(SYSTEMS))
def test_no_presolved_answer_in_prompt(system, task, monkeypatch):
    prompt = SYSTEMS[system](task, monkeypatch)
    assert not PREFILLED_FORMULA.search(prompt), f"{system}/{task.id}: pre-filled FORMULA line"
    assert not SOLVED_RETURN.search(prompt), f"{system}/{task.id}: `return <expr>` in prompt"


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
@pytest.mark.parametrize("system", list(SYSTEMS))
def test_task_information_present(system, task, monkeypatch):
    prompt = SYSTEMS[system](task, monkeypatch)
    needed = [task.description, *task.variables,
              *map(str, task.constants), *map(str, task.constants.values())]
    missing = [n for n in needed if n not in prompt]
    assert not missing, f"{system}/{task.id}: task information missing from prompt: {missing}"


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
@pytest.mark.parametrize("system", list(SYSTEMS))
def test_scaffold_has_no_extra_numbers(system, task, monkeypatch):
    prompt = SYSTEMS[system](task, monkeypatch)
    extra = re.findall(r"\d+\.\d+|\d{2,}", _scaffold(prompt, task))
    assert not extra, (
        f"{system}/{task.id}: numbers in the scaffold beyond the task text: {extra}. "
        "If this is legitimate scaffolding, allow-list it; otherwise it is hidden information."
    )


@pytest.mark.parametrize("task", TASKS[:3], ids=lambda t: t.id)
def test_cross_system_diff_report(task, monkeypatch):
    """Informational: print how the two systems' scaffolding differs (run with -s)."""
    a = _scaffold(_baseline_prompt(task, monkeypatch), task).splitlines()
    b = _scaffold(_hybrid_prompt(task, monkeypatch), task).splitlines()
    diff = "\n".join(difflib.unified_diff(a, b, "baseline", "hybrid_local_fallback", lineterm=""))
    print(f"\n===== {task.id}: baseline vs hybrid scaffolding =====\n{diff or '(identical)'}")


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
@pytest.mark.parametrize("system", list(SYSTEMS))
def test_hints_cannot_be_reenabled_by_flags(system, task, monkeypatch):
    """Deleted means deleted: even with the hint flag off under ALLOW_LEGACY=1, no system
    may put equation-specific text back into its prompt. (HARDCODED stays 1 so the
    baseline still reaches the LLM and the prompt can be captured.)"""
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", "0")
    prompt = SYSTEMS[system](task, monkeypatch)
    hits = [x for x in FORBIDDEN if x in prompt]
    assert not hits, f"{system}/{task.id}: hint text returns when the flag is off: {hits}"
