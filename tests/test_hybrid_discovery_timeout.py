"""Regression tests for HybridDiscovery timeout handling."""

from collections import defaultdict
from unittest.mock import Mock

import numpy as np
import pytest


def test_timeout_stops_retries_and_preserves_best_result():
    from hypatiax.tools.symbolic.hybrid_system_v50_2 import (
        HybridDiscoverySystem,
    )

    system = HybridDiscoverySystem.__new__(HybridDiscoverySystem)
    system.max_retries = 4
    system._pysr_deterministic = False
    system.enable_physics_fallback = False
    system.complexity_penalty_threshold = 20
    system.stats = defaultdict(int)

    # This must remain below the configured early-stop threshold while
    # still meeting the final best-result acceptance threshold (0.97).
    best = {
        "expression": "x + 1",
        "r2_score": 0.975,
        "llm_mode": "none",
    }

    engine = Mock()
    engine.discover.side_effect = [
        best,
        TimeoutError("PySR timed out"),
    ]
    system.symbolic_engine = engine

    result = system._discover_with_retry(
        X=np.array([[1.0], [2.0], [3.0]]),
        y=np.array([2.0, 3.0, 4.0]),
        variable_names=["x"],
        variable_descriptions={},
        variable_units={},
    )

    assert engine.discover.call_count == 2
    assert result["expression"] == "x + 1"
    assert result["r2_score"] == pytest.approx(0.975)


def test_subprocess_timeout_sets_worker_budget_and_kills_process_group(
    monkeypatch,
):
    import os
    import signal
    import subprocess

    import hypatiax.experiments.benchmarks.run_comparative_suite_benchmark_pca as bench

    captured = {}

    class FakeProcess:
        pid = 43210

        def __init__(self):
            self.communicate_calls = 0

        def communicate(self, **kwargs):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(cmd="worker", timeout=3)
            return b"", b""

        def kill(self):
            captured["fallback_kill"] = True

    fake_process = FakeProcess()

    def fake_popen(*args, **kwargs):
        captured["env"] = kwargs["env"]
        captured["start_new_session"] = kwargs["start_new_session"]
        return fake_process

    # subprocess is imported locally by the function under test.
    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(os, "getpgid", lambda pid: 43210)

    def fake_killpg(pgid, sig):
        captured["killed_group"] = (pgid, sig)

    monkeypatch.setattr(os, "killpg", fake_killpg)

    result = bench._run_pysr_in_subprocess(
        method="hybrid_v50_2",
        X=np.array([[1.0], [2.0]]),
        y=np.array([2.0, 3.0]),
        var_names=["x"],
        description="timeout regression",
        metadata={},
        extra_kwargs={"pysr_timeout": 17},
        timeout=3,
    )

    assert captured["env"]["PYSR_TIMEOUT"] == "17"
    assert captured["start_new_session"] is True
    assert captured["killed_group"] == (43210, signal.SIGKILL)
    assert result["success"] is False
    assert "timed out after 3s" in result["error"]
    assert fake_process.communicate_calls == 2
