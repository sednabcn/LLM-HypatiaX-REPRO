"""L03 / L52: the provenance gate must fail unaudited LLM rows, and the ablation hypatia-arm row
builder must emit the fields the gate reads. No torch / API key needed."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "scripts" / "audit_checks" / "01_provenance_gate.py"
ABL = ROOT / "hypatiax" / "experiments" / "benchmarks" / "exp1_ablation.py"


def _run(tmp_path, rows, flags=None):
    doc = {"results": rows}
    if flags is not None:
        doc["r2_sign_flip_enabled"] = flags
    f = tmp_path / "rows.json"
    f.write_text(json.dumps(doc))
    return subprocess.run([sys.executable, str(GATE), str(f)], capture_output=True, text=True).returncode


def test_gate_passes_live_row(tmp_path):
    assert _run(tmp_path, [{"llm_called": True, "llm_source": "live", "bypass_kind": "live"}], "0") == 0


def test_gate_passes_non_llm_row(tmp_path):
    assert _run(tmp_path, [{"llm_called": False, "llm_source": None, "bypass_kind": "none"}], "0") == 0


def test_gate_fails_llm_row_without_source(tmp_path):
    assert _run(tmp_path, [{"llm_called": True, "llm_source": None, "bypass_kind": "live"}], "0") == 1


def test_gate_fails_bad_sources(tmp_path):
    for bad in ("local_fallback", "hardcoded", "frozen_cache_unknown_origin"):
        assert _run(tmp_path, [{"llm_called": True, "llm_source": bad}], "0") == 1, bad


def test_gate_fails_active_sign_flip(tmp_path):
    assert _run(tmp_path, [{"llm_called": True, "llm_source": "live"}], "1") == 1


def test_ablation_row_emits_gate_fields():
    src = ABL.read_text(encoding="utf-8")
    for key in ("llm_called", "bypass_kind", "llm_source", "llm_model", "llm_temperature"):
        assert re.search(rf'"{key}"\s*:', src), f"exp1_ablation row builder lacks {key}"
