"""Regression coverage for native V60 metadata crossing the protocol boundary."""

from pathlib import Path


def test_v60_compatibility_status_is_preserved_in_method_result_metadata():
    repository_root = Path(__file__).resolve().parents[1]
    runner = (
        repository_root
        / "hypatiax"
        / "experiments"
        / "benchmarks"
        / "run_comparative_suite_benchmark_v2.py"
    )
    source = runner.read_text(encoding="utf-8")
    passthrough = (
        '"v50_2_compatibility_result": '
        'result.get("v50_2_compatibility_result")'
    )

    # Preserve the explicit V60/V50.2 separation marker for both successful
    # native handoffs and failed discovery results in the protocol JSON.
    assert source.count(passthrough) == 2
