"""Environment gate: the suite needs torch, anthropic and sympy.

Without them ~280 tests error at collection with unrelated-looking tracebacks.
This test fails with one explicit message instead (CI also runs the same check
before pytest, see .github/workflows/ci_tests.yml).
"""
import importlib

import pytest


@pytest.mark.parametrize("module", ["torch", "anthropic", "sympy", "numpy", "scipy", "sklearn", "pandas", "yaml"])
def test_dependency_importable(module):
    try:
        importlib.import_module(module)
    except ImportError as exc:  # pragma: no cover
        pytest.fail(f"required dependency '{module}' is not installed: {exc}. "
                    f"Run the suite in the CI environment (see ci_tests.yml).")
