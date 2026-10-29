"""LLM hypotheses must be scored in the same (log10) space the engine fits in."""
import numpy as np
import pytest

se = pytest.importorskip("hypatiax.tools.symbolic.symbolic_engine")
Engine, Hyp = se.SymbolicEngineWithLLM, se.EquationHypothesis
NAMES = ["m1", "m2", "r"]


def _slog(a):
    return np.sign(a) * np.log10(np.abs(a) + 1.0)


@pytest.fixture(scope="module")
def grav():
    rng = np.random.RandomState(0)
    X = np.column_stack([rng.uniform(1e10, 1e12, 160), rng.uniform(1e10, 1e12, 160),
                         rng.uniform(1e6, 1e8, 160)])
    y = 6.674e-11 * X[:, 0] * X[:, 1] / X[:, 2] ** 2
    return X, y, _slog(X), _slog(y)


def _engine(ctx):
    e = Engine.__new__(Engine)          # skip __init__: no PySR / API needed
    e._fixd_ctx = ctx
    return e


def _score(e, eq, Xf, yf):
    return e._evaluate_hypotheses([Hyp(eq, 0.9, "t")], Xf, yf, NAMES).r2_score


CTX = {"safe": True, "x_log_flags": [True, True, True], "y_log": True}


def test_old_behaviour_discards_a_correct_formula(grav):
    _, _, Xf, yf = grav
    assert _score(_engine(None), "6.674e-11 * m1 * m2 / r**2", Xf, yf) < 0.5   # the bug


def test_correct_formula_scores_high_in_fit_space(grav):
    _, _, Xf, yf = grav
    assert _score(_engine(CTX), "6.674e-11 * m1 * m2 / r**2", Xf, yf) > 0.99


def test_wrong_formula_still_scores_low(grav):
    _, _, Xf, yf = grav
    assert _score(_engine(CTX), "6.674e-11 * m1 * m2 / r**2 * g_n", Xf, yf) < 0.5


def test_returned_equation_is_evaluable_on_scaled_x(grav):
    _, _, Xf, yf = grav
    e = _engine(CTX)
    best = e._evaluate_hypotheses([Hyp("6.674e-11 * m1 * m2 / r**2", 0.9, "t")], Xf, yf, NAMES)
    assert best.raw_equation == "6.674e-11 * m1 * m2 / r**2"
    pred = e._predict_from_equation(best.equation, Xf, NAMES)
    assert np.corrcoef(pred, yf)[0, 1] > 0.99


def test_unsafe_context_leaves_equation_untouched(grav):
    _, _, Xf, yf = grav
    ctx = {"safe": False, "x_log_flags": [True, True, True], "y_log": True}
    e = _engine(ctx)
    best = e._evaluate_hypotheses([Hyp("m1 * m2", 0.9, "t")], Xf, yf, NAMES)
    assert best.equation == "m1 * m2"


def test_variable_names_only_substituted_as_whole_words():
    out = Engine._llm_to_fit_space("sqrt(r) + m1*r", ["m1", "r"], [True, True], False)
    assert "sqrt((sign(r)*(10**abs(r)-1)))" in out and out.count("10**abs(m1)") == 1 and "sq(" not in out


def test_negative_noisy_target_is_mapped(grav):
    """Noisy targets go negative; the signed log10 mapping must still score a correct formula high."""
    X, y, Xf, _ = grav
    rng = np.random.RandomState(1)
    y_noisy = y + rng.normal(0, 0.05 * y.std(), y.size)
    assert (y_noisy < 0).any()
    yf = _slog(y_noisy)
    e = _engine(CTX)
    assert e._evaluate_hypotheses([Hyp("6.674e-11 * m1 * m2 / r**2", 0.9, "t")],
                                  Xf, yf, NAMES).r2_score > 0.9
    assert e._evaluate_hypotheses([Hyp("6.674e-11 * m1 * m2 / r**2 * g_n", 0.9, "t")],
                                  Xf, yf, NAMES).r2_score < 0.5


def test_prompt_withholds_name_and_worked_example(monkeypatch):
    monkeypatch.delenv("HYPATIAX_DISABLE_PROMPT_HINTS", raising=False)   # unset == clean
    eng = se.IntegratedLLMEngine.__new__(se.IntegratedLLMEngine)
    p = eng._build_prompt("physics", ["m", "v"], "Kinetic Energy", {}, 3)
    assert "Kinetic Energy" not in p and "0.5 * m * v**2" not in p and "kinetic" not in p.lower()
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", "0")
    legacy = eng._build_prompt("physics", ["m", "v"], "Kinetic Energy", {}, 3)
    assert "Kinetic Energy" in legacy               # legacy mode restores the name ...
    assert "0.5 * m * v**2" not in legacy           # ... but the worked example is a placeholder in EVERY mode
