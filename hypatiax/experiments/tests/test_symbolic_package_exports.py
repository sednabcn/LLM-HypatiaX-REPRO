"""Regression tests for the public symbolic package interface."""

import builtins
import importlib
import sys


def test_symbolic_public_exports_resolve():
    from hypatiax.tools.symbolic import (
        DiscoveryConfig,
        LLMConfig,
        PhysicsAwareRegressor,
        SymbolicEngine,
        SymbolicEngineWithLLM,
    )

    assert PhysicsAwareRegressor.__name__ == "PhysicsAwareRegressor"
    assert SymbolicEngine.__name__ == "SymbolicEngine"
    assert SymbolicEngineWithLLM.__name__ == "SymbolicEngineWithLLM"
    assert DiscoveryConfig.__name__ == "DiscoveryConfig"
    assert LLMConfig.__name__ == "LLMConfig"


def test_importing_symbolic_engine_does_not_import_pysr(monkeypatch):
    module_name = "hypatiax.tools.symbolic.symbolic_engine"
    sys.modules.pop(module_name, None)
    original_import = builtins.__import__

    def reject_eager_pysr(name, *args, **kwargs):
        if name == "pysr" or name.startswith("pysr."):
            raise AssertionError("PySR must only be imported inside the discovery method")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_eager_pysr)
    importlib.import_module(module_name)
