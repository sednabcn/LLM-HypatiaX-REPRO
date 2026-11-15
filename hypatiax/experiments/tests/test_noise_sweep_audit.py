"""AUDIT B5: noise-sweep aggregation must not crash on non-finite rows, must not adopt
another seed's result file, and must write strict JSON."""
import importlib.util, json, sys
from pathlib import Path
import pytest

BM = Path(__file__).resolve().parents[1] / "benchmarks" / "run_noise_sweep_benchmark.py"


@pytest.fixture(scope="module")
def ns():
    try:
        spec = importlib.util.spec_from_file_location("noise_sweep_mod", BM)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except ImportError as e:
        pytest.skip(f"hypatiax core not importable here: {e}")


def _result(path, sigma, seed, r2s):
    tests = []
    for i, r2 in enumerate(r2s):
        tests.append({"metadata": {"equation_name": f"eq{i}"}, "description": f"eq{i}",
                      "results": {"M": {"r2": r2, "rmse": None if r2 is None else 0.1,
                                        "success": r2 is not None, "time": 1.0}}})
    path.write_text(json.dumps({"protocol": {"noise_level": sigma, "noise_seed": seed,
                                             "noise_injected_equations": len(r2s),
                                             "scored_on": "noisy targets (train and test)"},
                                "tests": tests}))
    return path


def test_aggregate_report_and_write_with_nonfinite_rows(ns, tmp_path, monkeypatch, capsys):
    p = _result(tmp_path / "protocol_core_noisy_a.json", 0.05, 42, [0.99, None, None, -50.0])
    agg = ns._aggregate_results([0.05], {0.05: p}, threshold_fn=lambda s: 0.99)
    ns._print_noise_sweep_table(agg)          # used to raise TypeError (None sort / format)
    cf = agg["per_noise"]["0.0500"]["catastrophic_failures"]
    assert [c["r2"] for c in cf][:2] == [None, None]
    pe = agg["per_noise"]["0.0500"]["per_equation"]
    assert pe["eq1"]["M"]["catastrophic"] is True      # null r2 counted like the aggregate does
    assert agg["per_noise"]["0.0500"]["noise_protocol"]["noise_injected_equations"] == 4
    monkeypatch.setattr(ns, "_RESULTS_DIR", tmp_path)
    out = ns._save_sweep_json(agg, "TS")
    json.loads(out.read_text(), parse_constant=lambda c: pytest.fail(f"bare {c} in output"))


def test_nonfinite_floats_written_as_null(ns):
    assert ns._nulls({"a": float("-inf"), "b": [float("nan"), 1.0]}) == {"a": None, "b": [None, 1.0]}


def test_other_seed_result_is_not_matched(ns, tmp_path):
    p = _result(tmp_path / "protocol_core_noisy_b.json", 0.01, 99, [0.99])
    assert ns._result_matches(p, 0.01, seed=99)
    assert not ns._result_matches(p, 0.01, seed=42)
    assert ns._result_matches(p, 0.01)                 # seed unspecified -> unchanged behaviour
