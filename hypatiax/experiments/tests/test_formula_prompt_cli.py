"""Offline regression coverage for the formula-prompt CLI."""
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "test_formula_prompt.py"
SPEC = importlib.util.spec_from_file_location("formula_prompt_cli", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_production_prompt_contract_offline():
    result = MODULE._prompt_contract()
    assert result["status"] == "passed"
    assert result["api_calls"] == 0
    assert len(result["prompt_sha256"]) == 64
    assert result["checks"]["undeclared_parameters_rejected"] is True
