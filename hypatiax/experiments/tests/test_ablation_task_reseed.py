"""Static checks for AUDIT L57/L72 (per-task reseed) and the sanitized_vars dedup."""
import re
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "benchmarks" / "exp1_ablation.py").read_text()


def test_sanitized_vars_key_unique_in_row():
    assert SRC.count('"sanitized_vars"') == 1


def test_reseed_helper_defined():
    assert "def _reseed_for_task(" in SRC


def test_reseed_called_before_discover_with_eq_seed():
    i = SRC.index("_reseed_for_task(eq_seed)")
    j = SRC.index("hybrid.discover(")
    assert i < j


def test_reseed_not_inside_retry_path():
    # discover() itself must not be reseeded (PySR retries would repeat identically)
    assert len(re.findall(r"_reseed_for_task\(", SRC)) == 2  # def + one call
