"""Engine-level tests for the seed audit. Run from the repo root: python -m pytest -q test_engine_seed_audit.py
(needs fake_probe.py next to it: it installs the stand-in PySR and imports the engine)."""
import json
import numpy as np
import fake_probe as F

E, G, X, y = F.E, F.G, F.X, F.y
CFG = lambda: E.DiscoveryConfig(niterations=2, pysr_timeout=5)


def test_fit_time_fallback_is_recorded(monkeypatch):
    orig = F.FakePySR.fit
    def failing_fit(self, X, y, **kw):
        if self.guesses:
            raise RuntimeError("JuliaError: boom")
        return orig(self, X, y, **kw)
    monkeypatch.setattr(F.FakePySR, "fit", failing_fit)
    G.reset_audit()
    res = E.SymbolicEngine(CFG()).discover(X, y, ["x0"], equation_name="t", random_state=1,
                                           seed_expressions=["x0*x0"])
    row = G.drain_audit()
    assert res["expression"] != "DISCOVERY_FAILED"          # the retry still produced a result
    assert row["guess_fit_fallback"] is True                 # ...but it is no longer only in the log
    assert res["guess_audit"]["guess_fit_fallback"] is True
    assert row["guesses_requested"] == row["guesses_used"] + row["guesses_dropped"] == 1


def test_audit_survives_llm_better_branch():
    eng = E.SymbolicEngineWithLLM(CFG(), llm_mode="hybrid")
    class LLM:
        last_call_attempted, last_error = True, None
        config = E.LLMConfig(enabled=True)
        def generate_hypotheses(self, **kw):
            return [E.EquationHypothesis("x0 + 0.0*x0**0.75", 0.5, "r")]
    class Pat:
        def analyze(self, *a): return {}
    eng.llm_mode, eng.llm_engine, eng.pattern_analyzer = "hybrid", LLM(), Pat()
    eng._LLM_ACCEPT_R2 = float("inf")                       # force the PySR phase
    G.reset_audit()
    res = eng.discover(X, y, ["x0"], equation_name="t", random_state=1)
    assert res["llm_mode"] == "hybrid_llm_better"            # the branch that rebuilds the dict
    a = res["guess_audit"]
    assert (a["guesses_requested"], a["guesses_used"], a["guesses_dropped"]) == (1, 0, 1)
    assert a["guess_dropped_reasons"] == ["needs_pow"] and a["guess_fit_fallback"] is False
    assert G.drain_audit()["guesses_dropped"] == 1


def test_replay_cache_one_sample_per_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("HYPATIAX_LLM_REPLAY_DIR", str(tmp_path))
    eng = E.IntegratedLLMEngine.__new__(E.IntegratedLLMEngine)
    eng.config, eng.client, eng.last_call_attempted, eng.last_error = E.LLMConfig(enabled=True), object(), False, None
    calls = []
    def fake_call(prompt):
        calls.append(prompt)
        return json.dumps([{"equation": f"x0*{len(calls)}", "confidence": .5, "reasoning": "r"}])
    eng._call_llm = fake_call
    kw = dict(domain="d", variables=["x0"], description="t", data_patterns={"a": 1})
    h1 = eng.generate_hypotheses(**kw)
    h2 = eng.generate_hypotheses(**kw)                       # second arm
    assert len(calls) == 1 and h1[0].equation == h2[0].equation and eng.last_response_replayed
    assert eng.last_call_attempted is True                   # G3 still sees a call
    eng.generate_hypotheses(**dict(kw, data_patterns={"a": 2}))   # different data -> new sample
    assert len(calls) == 2


def test_replay_off_by_default(monkeypatch):
    monkeypatch.delenv("HYPATIAX_LLM_REPLAY_DIR", raising=False)
    eng = E.IntegratedLLMEngine.__new__(E.IntegratedLLMEngine)
    eng.config, eng.client, eng.last_call_attempted, eng.last_error = E.LLMConfig(enabled=True), object(), False, None
    n = []
    eng._call_llm = lambda p: (n.append(1), "[]")[1]
    eng.generate_hypotheses("d", ["x0"], "t", {}); eng.generate_hypotheses("d", ["x0"], "t", {})
    assert len(n) == 2


def test_timeout_is_not_a_seed_fallback(monkeypatch):
    calls = []
    orig = F.FakePySR.fit
    def timing_out_fit(self, X, y, **kw):
        calls.append(bool(self.guesses))
        if self.guesses:
            raise TimeoutError("Wall-clock limit of 600s exceeded")
        return orig(self, X, y, **kw)
    monkeypatch.setattr(F.FakePySR, "fit", timing_out_fit)
    G.reset_audit()
    res = E.SymbolicEngine(CFG()).discover(X, y, ["x0"], equation_name="t", random_state=1,
                                           seed_expressions=["x0*x0"])
    assert calls == [True]                                   # no second, unseeded attempt
    assert res["expression"] == "DISCOVERY_FAILED"           # same as a timeout without a seed
    assert res["guess_audit"]["guess_fit_fallback"] is False  # not mislabelled as a bad seed
