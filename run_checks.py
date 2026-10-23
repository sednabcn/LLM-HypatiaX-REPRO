"""Run test_no_equation_hints.py without pytest (offline fallback)."""
import sys, types, os, importlib, itertools
pt = types.ModuleType("pytest")
pt.fixture = lambda f: f
class _M:
    @staticmethod
    def parametrize(names, vals):
        def d(f): f.__params = getattr(f, "_p", []) + [(names, vals)]; f._p = f.__params; return f
        return d
pt.mark = _M
sys.modules["pytest"] = pt
import test_no_equation_hints as t

class MP:
    def __init__(self): self.undo = []
    def setenv(self, k, v): self.undo.append((k, os.environ.get(k))); os.environ[k] = v
    def restore(self):
        for k, v in reversed(self.undo):
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

def run(f):
    plist = getattr(f, "_p", [])
    # decorators apply bottom-up; build the cartesian product of parameter sets
    sets = []
    for names, vals in plist:
        ns = [n.strip() for n in names.split(",")]
        sets.append([dict(zip(ns, v if len(ns) > 1 else (v,))) for v in vals])
    ok = bad = 0
    for combo in itertools.product(*sets) if sets else [()]:
        kw = {}
        for c in combo: kw.update(c)
        mp = MP()
        try:
            b = t.baseline.__wrapped__(mp) if hasattr(t.baseline, "__wrapped__") else t.baseline(mp)
            f(b, mp, **kw) if "monkeypatch" in f.__code__.co_varnames else f(b, **kw)
            ok += 1
        except AssertionError as e:
            bad += 1; print("  FAIL", {k: v for k, v in kw.items() if k in ("desc", "flags")}, str(e)[:120])
        finally:
            mp.restore()
    print(f"{f.__name__}: {ok} passed, {bad} failed")
    return bad

bad = run(t.test_no_equation_specific_hints) + run(t.test_prompt_identical_across_flag_values)
sys.exit(1 if bad else 0)
