"""M4 exclusion: derived comparison/winner fields must agree with the exclude_from_reported_results flags."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("close_m4_exclusion", ROOT / "scripts/close_m4_exclusion.py")
cx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cx)

M4 = "HybridSystemLLMNN all-domains (core)"


def _res(r2, time=1.0, formula="f", **kw):
    return {"success": True, "r2": r2, "time": time, "formula": formula, **kw}


def test_excluded_m4_cannot_win():
    t = {"results": {"A": _res(0.99), M4: _res(1.0, formula="N/A", exclude_from_reported_results=True),
                     "B": _res(0.95)},
         "comparison": {"winner": M4, "scores": {}}, "winner": M4}
    assert cx.fix_test(t) is True
    assert t["winner"] == t["comparison"]["winner"] == "A"
    assert M4 not in t["comparison"]["scores"] and M4 not in t["comparison"]["rankings"]
    assert [a["method"] for a in t["comparison"]["advantages"]] == ["B"]
    assert t["comparison"]["winner_before_exclusion"] == M4
    assert cx.fix_test(t) is False          # idempotent


def test_per_method_values_moved_not_lost():
    t = {"results": {"A": _res(0.9), M4: _res(1.0, exclude_from_reported_results=True)},
         "comparison": {"winner": M4}, "winner": M4, "extrap_r2_far": {"A": 0.5, M4: 0.97}}
    cx.fix_test(t)
    assert t["extrap_r2_far"][M4] is None
    assert t["excluded_method_values"]["extrap_r2_far"][M4] == 0.97


def test_all_excluded_gives_no_winner():
    t = {"results": {M4: _res(1.0, exclude_from_reported_results=True)}, "comparison": {"winner": M4}, "winner": M4}
    cx.fix_test(t)
    assert t["winner"] == "None"


def test_stored_comparisons_reproduced_by_compare():
    n, ok, bad = cx.selftest()
    assert n > 0 and ok == n, bad[:3]


def test_repo_has_no_stale_m4_comparisons_or_csv_rows():
    assert cx.stale() == []
    assert cx.csv_unflagged() == []
