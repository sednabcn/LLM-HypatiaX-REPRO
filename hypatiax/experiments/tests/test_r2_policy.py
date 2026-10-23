"""R^2 policy tests for the old repo (ported from LLM-HypatiaX-Hybrid).

1. canonical policy of hypatiax/core/r2_canonical.py
2. mechanics of scripts/migrate_r2_repro.py (rewrite keeps contracts)
3. migration checklist: the central scorers must delegate (fails until
   ``python scripts/migrate_r2_repro.py --apply`` has been run)
4. ratchet: no NEW file may compute ``ss_tot``; legacy files are listed in
   r2_legacy_baseline.json (regenerate with
   ``python scripts/migrate_r2_repro.py --write-baseline`` after migrating
   more of them -- the list may only shrink).
"""
import ast
import importlib.util
import json
import math
import pathlib
import re
import textwrap
import warnings

import numpy as np
import pytest

from hypatiax.core.r2_canonical import (
    THRESH_PRIMARY, THRESH_STRICT, is_recovered, r2, r2_checked, r2_scored,
    selection_score,
)

ROOT = pathlib.Path(__file__).resolve().parents[3]
RNG = np.random.default_rng(0)


# ------------------------------------------------------------------ 1. policy
def test_exact_formula_recovers():
    y = RNG.normal(size=200)
    val, status = r2_checked(y, y.copy())
    assert status == "ok" and val == pytest.approx(1.0, abs=1e-12)
    assert is_recovered(val, THRESH_PRIMARY) and is_recovered(val, THRESH_STRICT)


def test_constant_target_is_undefined_never_recovered():
    y = np.full(100, 5.0)
    for pred in (y.copy(), y + 100.0):
        val, status = r2_checked(y, pred)
        assert math.isnan(val) and status == "degenerate_target"
        assert not is_recovered(val)


def test_tiny_scale_varying_target_is_scored():
    for scale in (1e-11, 1e-19, 1e-23):           # Newton, Photon, Zeeman
        y = np.linspace(1.0, 2.0, 50) * scale
        assert r2(y, y) == pytest.approx(1.0, abs=1e-12)
        assert not is_recovered(r2(y, y * 1.5))


def test_failures_are_minus_inf_not_undefined():
    y = RNG.normal(size=20)
    p = y.copy(); p[3] = np.nan
    assert r2_checked(y, p) == (float("-inf"), "nonfinite_pred")
    assert r2_checked(np.ones(5), np.ones(4)) == (float("-inf"), "bad_shape")


def test_constant_prediction_is_scored_not_failed():
    # legacy _v2/_pca scorers returned -inf here; canonical scores it normally
    y = RNG.normal(size=100)
    val = r2(y, np.full_like(y, y.mean()))
    assert val == pytest.approx(0.0, abs=1e-12)


def test_selection_score_sends_undefined_to_bottom():
    assert selection_score(float("nan")) == float("-inf")
    assert selection_score(0.7) == 0.7


# --------------------------------------------------------------- sign flip
def test_sign_flip_is_off_by_default(monkeypatch):
    monkeypatch.delenv("HYPATIAX_R2_SIGN_FLIP", raising=False)
    y = RNG.normal(size=100)
    val, status = r2_scored(y, -y)
    assert status == "ok" and val < -1.0 and not is_recovered(val)


def test_sign_flip_opt_in_reproduces_legacy_scoring(monkeypatch):
    y = RNG.normal(size=100)
    assert r2_scored(y, -y, sign_flip=True)[0] == pytest.approx(1.0, abs=1e-12)
    monkeypatch.setenv("HYPATIAX_R2_SIGN_FLIP", "1")
    assert r2_scored(y, -y)[0] == pytest.approx(1.0, abs=1e-12)
    # never makes a good score worse, never touches failures
    assert r2_scored(y, y, sign_flip=True)[0] == pytest.approx(1.0, abs=1e-12)
    p = y.copy(); p[0] = np.inf
    assert r2_scored(y, p, sign_flip=True)[0] == float("-inf")


# ------------------------------------------------------------ benchmark guards
def test_out_of_range_and_catastrophic_predictions_are_minus_inf():
    # one divergent prediction must not produce a -1e155 that swamps a mean
    y = RNG.normal(size=100) + 3
    assert r2_scored(y, y * 1e101) == (float("-inf"), "pred_out_of_range")
    assert r2_scored(y, y + 1e3) == (float("-inf"), "catastrophic")
    assert r2_scored(y, y + 1e3, floor=None)[1] == "ok"        # guard can be disabled
    assert r2_scored(y, 1.5 * y)[0] == pytest.approx(r2(y, 1.5 * y))   # ordinary misses untouched


def test_plain_r2_has_no_benchmark_guards():
    y = RNG.normal(size=100) + 3
    assert math.isfinite(r2(y, y + 1e3))                       # canonical r2 itself never clamps


# ------------------------------------------------------ 2. migration mechanics
def _load_script():
    path = ROOT / "scripts" / "migrate_r2_repro.py"
    if not path.is_file():
        pytest.skip("scripts/migrate_r2_repro.py not present")
    spec = importlib.util.spec_from_file_location("migrate_r2_repro", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Shaped like the real scorers (a method, a documented module function, and
# the Optional-returning helper), incl. the drifted bodies seen in the wild.
LEGACY_SRC = textwrap.dedent('''
    import numpy as np

    class Base:
        def _safe_r2(self, y_true, y_pred) -> float:
            y_pred = np.asarray(y_pred, dtype=float)
            # Guard: reject non-finite predictions
            if np.any(~np.isfinite(y_pred)):
                return float("-inf")
            if np.std(y_pred) < 1e-30:
                return float("-inf")
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            if ss_tot < 1e-10:
                return 1.0
            return float(1 - np.sum((y_true - y_pred) ** 2) / ss_tot)

        def other(self):
            return 7

    def _far_r2(y_true, y_pred):
        """Returns None when degenerate."""
        y_pred = np.asarray(y_pred, dtype=float)
        if np.std(y_pred) < 1e-30:
            return None
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return float(1 - np.sum((y_true - y_pred) ** 2) / ss_tot)
''')


def _migrated_namespace(kinds):
    mod = _load_script()
    src = LEGACY_SRC
    for name, kind in kinds:
        src, msg = mod.rewrite(src, name, kind)
        assert src is not None and msg.startswith("rewrite"), msg
    ns = {}
    exec(compile(src, "<migrated>", "exec"), ns)
    return mod, src, ns


def test_rewrite_float_contract_and_idempotence():
    mod, src, ns = _migrated_namespace([("_safe_r2", "float")])
    ast.parse(src)
    assert "ss_tot" not in src.split("def _far_r2")[0]          # old body gone
    assert "def other" in src and "return 7" in src             # neighbours intact
    y = np.linspace(1, 2, 30)
    b = ns["Base"]()
    assert b._safe_r2(y, y) == pytest.approx(1.0)
    assert b._safe_r2(y, np.full(30, y.mean())) == pytest.approx(0.0, abs=1e-12)  # not -inf
    assert math.isnan(b._safe_r2(np.ones(30), np.ones(30)))                       # not 1.0
    assert b._safe_r2(y, np.where(np.arange(30) == 2, np.nan, y)) == float("-inf")
    assert b._safe_r2(y, y + 1e3) == float("-inf")             # catastrophic clamp kept
    again, msg = mod.rewrite(src, "_safe_r2", "float")
    assert again is None and msg == "already migrated"


def test_rewrite_optional_contract_keeps_docstring():
    mod, src, ns = _migrated_namespace([("_far_r2", "optional")])
    assert '"""Returns None when degenerate."""' in src
    y = np.linspace(1, 2, 30)
    assert ns["_far_r2"](y, y) == pytest.approx(1.0)
    assert ns["_far_r2"](np.ones(30), np.ones(30)) is None
    assert ns["_far_r2"](y, np.where(np.arange(30) == 2, np.inf, y)) is None
    assert ns["_far_r2"](y, y + 1e3) == float("-inf")          # scored, catastrophic != missing


def test_rewrite_float_raise_keeps_nonfinite_target_guard():
    mod, src, ns = _migrated_namespace([("_safe_r2", "float_raise")])
    y = np.linspace(1, 2, 30)
    bad = y.copy(); bad[0] = np.nan
    with pytest.raises(ValueError):
        ns["Base"]()._safe_r2(bad, y)


def test_rewrite_refuses_ambiguous_or_missing_names():
    mod = _load_script()
    assert mod.rewrite(LEGACY_SRC, "nope", "float")[0] is None
    two = LEGACY_SRC + "\ndef _far_r2(a, b):\n    return 0\n"
    new, msg = mod.rewrite(two, "_far_r2", "optional")
    assert new is None and msg.startswith("ERROR")


# ------------------------------------------------- 3. migration checklist
def test_central_scorers_delegate_to_canonical():
    """Fails until `python scripts/migrate_r2_repro.py --apply` has been run;
    the failure message is the checklist."""
    mod = _load_script()
    todo = []
    for rel, name, _kind in mod.TARGETS:
        path = ROOT / rel
        if not path.is_file():
            continue
        src = path.read_text()
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.FunctionDef) and n.name == name:
                seg = ast.get_source_segment(src, n) or ""
                if mod.MARKER not in seg:
                    todo.append(f"{rel}::{name}")
    assert not todo, "not yet using hypatiax.core.r2_canonical:\n  " + "\n  ".join(todo)


# ------------------------------------------------------------ 4. ratchet
BASELINE = pathlib.Path(__file__).with_name("r2_legacy_baseline.json")
_SS_TOT = re.compile(r"\bss_tot\b")


def _files_with_ss_tot():
    out = set()
    for path in (ROOT / "hypatiax").rglob("*.py"):
        parts = set(path.parts)
        if "__pycache__" in parts or "tests" in parts or path.name == "r2_canonical.py":
            continue
        if _SS_TOT.search(path.read_text(errors="ignore")):
            out.add(path.relative_to(ROOT).as_posix())
    return out


def test_no_new_r2_reimplementations():
    if not BASELINE.is_file():
        pytest.skip("r2_legacy_baseline.json missing; run migrate_r2_repro.py --write-baseline")
    allowed = set(json.loads(BASELINE.read_text())["files"])
    current = _files_with_ss_tot()
    new = sorted(current - allowed)
    assert not new, ("R^2 re-implemented in files not in the legacy baseline "
                     "(import hypatiax.core.r2_canonical instead, or, if this is a "
                     "pre-existing copy, regenerate the baseline):\n  " + "\n  ".join(new))
    gone = sorted(allowed - current)
    if gone:
        warnings.warn("legacy R^2 copies migrated; shrink the baseline "
                      "(migrate_r2_repro.py --write-baseline): " + ", ".join(gone))


# ------------------------------------------------ adaptive_config (hand-migrated)
def test_adaptive_config_uses_canonical_scorer_and_nan_safe_selection():
    src = (ROOT / "hypatiax/core/training/adaptive_config.py").read_text()
    assert "ss_tot" not in src and "r2_scored" in src
    assert "selection_score" in src          # nan/-inf must lose the best-of-seeds comparison
    # the old absolute floor scored a tiny-scale target as 0.0/1.0 whatever the model did:
    y = np.linspace(1.0, 2.0, 50) * 1e-11
    old = 1.0 if np.sum((y - 0.0) ** 2) < 1e-10 else 0.0       # what the 1e-10 guard returned
    assert old == 1.0 and not is_recovered(r2(y, y * 1.5))     # canonical: a wrong model is not "1.0"
