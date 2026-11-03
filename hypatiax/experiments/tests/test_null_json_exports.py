"""AUDIT L37: result exports write null + status, never bare -Infinity; the
resume checkpoint stays float-typed. Helper block is exec'd from each suite."""
import io
import json
import re
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[1] / "benchmarks"
SUITES = ["run_comparative_suite_benchmark_v2.py", "run_comparative_suite_benchmark_pca.py"]
_RX = re.compile(r"# --- BEGIN null-json helpers.*?# --- END null-json helpers[^\n]*\n", re.S)


def _ns(name):
    m = _RX.search((BENCH / name).read_text(encoding="utf-8"))
    assert m, f"{name}: helper block missing"
    ns = {"json": json}
    exec(m.group(0), ns)
    return ns


@pytest.mark.parametrize("name", SUITES)
def test_helpers_write_strict_json_with_null(name):
    ns = _ns(name)
    buf = io.StringIO()
    ns["_dump_json_null"](
        {"r2": float("-inf"), "rmse": float("inf"), "x": [float("nan"), 0.5], "r2_status": ns["_status_of"](float("-inf"))},
        buf, indent=2)
    s = buf.getvalue()
    assert "Infinity" not in s and "NaN" not in s
    d = json.loads(s, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    assert d["r2"] is None and d["rmse"] is None and d["x"] == [None, 0.5]
    assert d["r2_status"] == "failed"


@pytest.mark.parametrize("name", SUITES)
def test_status_and_numpy_floats(name):
    np = pytest.importorskip("numpy")
    ns = _ns(name)
    assert ns["_status_of"](0.9) == "ok" and ns["_status_of"](None) == "failed"
    assert ns["_status_of"](True) == "failed"
    out = ns["_nulls"]({"a": np.float32("inf"), "b": np.float64("nan"), "c": np.float64(1.5), "d": 3})
    assert out == {"a": None, "b": None, "c": 1.5, "d": 3}


@pytest.mark.parametrize("name", SUITES)
def test_wiring_in_suite_source(name):
    t = (BENCH / name).read_text(encoding="utf-8")
    assert t.count("_dump_json_null(") == 4          # def + 3 export sites
    assert '"r2_status":    _status_of(self.r2)' in t and '"rmse_status":  _status_of(self.rmse)' in t
    # the resume checkpoint must remain a plain float dump (load_checkpoint reads it back)
    assert re.search(r"json\.dump\(payload, f, indent=2, default=str\)\n\s*os\.replace\(tmp, path\)", t)
