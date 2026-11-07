"""Isolated runtime tests for the archived HypatiaX maintenance scripts.

All filesystem-mutating cases use pytest's temporary directory; no archived
benchmark results or real source files are read or modified.
"""
import importlib.util
import sys
from pathlib import Path

import pytest


SOURCE_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = SOURCE_ROOT / "scripts"


def _load_script(filename, module_name):
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def close_script():
    return _load_script("close_m4_exclusion.py", "hypatiax_close_m4_exclusion_test")


@pytest.fixture
def migrate_script():
    return _load_script("migrate_r2_repro.py", "hypatiax_migrate_r2_repro_test")


def test_close_m4_recomputes_comparison_and_moves_excluded_values(close_script):
    excluded = "HybridSystemLLMNN"
    active = "Baseline"
    test = {
        "results": {
            excluded: {
                "success": True,
                "r2": 0.999,
                "time": 0.1,
                close_script.FLAG: True,
                "formula": None,
            },
            active: {"success": True, "r2": 0.8, "time": 0.2},
        },
        "comparison": {"winner": excluded, "scores": {excluded: 0.999, active: 0.8}},
        "winner": excluded,
        "extrap_r2_far": {excluded: 0.95, active: 0.7},
    }

    changed = close_script.fix_test(test)

    assert changed
    assert test["winner"] == active
    assert test["comparison"]["winner"] == active
    assert excluded not in test["comparison"]["scores"]
    assert test["extrap_r2_far"][excluded] is None
    assert test["excluded_method_values"]["extrap_r2_far"][excluded] == 0.95
    assert test["comparison"]["winner_before_exclusion"] == excluded
    assert close_script.fix_test(test) is False


def test_close_m4_csv_update_is_confined_to_temporary_file(close_script, tmp_path):
    csv_path = tmp_path / "noise_sweep.csv"
    csv_path.write_text(
        "method,r2\nHybridSystemLLMNN,0.99\nBaseline,0.8\n",
        encoding="utf-8",
    )

    # Dry run reports the rows to change but leaves the file byte-for-byte intact.
    before = csv_path.read_bytes()
    assert close_script.fix_csv(csv_path, apply=False) == 1
    assert csv_path.read_bytes() == before

    assert close_script.fix_csv(csv_path, apply=True) == 1
    rows, _, _ = close_script._csv_rows(csv_path)
    header = rows[0]
    m4 = rows[1]
    assert m4[header.index(close_script.FLAG)] == "True"
    assert m4[header.index("provenance_status")] == close_script.STATUS
    assert rows[2][header.index(close_script.FLAG)] == ""


def test_close_m4_check_detects_and_then_clears_stale_data(close_script, tmp_path, monkeypatch):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    data = {
        "tests": [{
            "description": "temporary fixture",
            "results": {
                "HybridSystemLLMNN": {
                    "success": True, "r2": 0.99,
                    close_script.FLAG: True,
                },
                "Baseline": {"success": True, "r2": 0.8},
            },
            "winner": "HybridSystemLLMNN",
            "comparison": {
                "winner": "HybridSystemLLMNN",
                "scores": {"HybridSystemLLMNN": 0.99, "Baseline": 0.8},
                "rankings": {"HybridSystemLLMNN": 1, "Baseline": 2},
                "advantages": [],
            },
        }]
    }
    import json

    (results_dir / "fixture.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(close_script, "RES", results_dir)

    assert len(close_script.stale()) == 1
    loaded = json.loads((results_dir / "fixture.json").read_text(encoding="utf-8"))
    close_script.fix_test(loaded["tests"][0])
    (results_dir / "fixture.json").write_text(json.dumps(loaded), encoding="utf-8")
    assert close_script.stale() == []


def test_migrate_rewrite_delegates_to_canonical_scorer(migrate_script):
    source = (
        "def legacy_score(y_true, y_pred):\n"
        '    """Keep this public docstring."""\n'
        "    return old_r2(y_true, y_pred)\n"
    )

    rewritten, message = migrate_script.rewrite(source, "legacy_score", "float")

    assert rewritten is not None, message
    assert "Keep this public docstring." in rewritten
    assert migrate_script.MARKER in rewritten
    assert "r2_scored(y_true, y_pred)" in rewritten
    compile(rewritten, "<rewritten-fixture>", "exec")


def test_migrate_rewrite_rejects_missing_or_ambiguous_functions(migrate_script):
    source = "def score(y_true, y_pred):\n    return 1.0\n"
    assert migrate_script.rewrite(source, "absent", "float")[0] is None

    ambiguous = source + "\n" + source.replace("score", "score")
    rewritten, message = migrate_script.rewrite(ambiguous, "score", "float")
    assert rewritten is None
    assert "ambiguous" in message


def test_migrate_apply_targets_only_changes_temporary_target(migrate_script, tmp_path, monkeypatch):
    relative = "hypatiax/core/metrics.py"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_text(
        "def compute_r2(y_true, y_pred):\n"
        "    return r2_checked(y_true, y_pred)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(migrate_script, "ROOT", tmp_path)
    monkeypatch.setattr(
        migrate_script,
        "TARGETS",
        ((relative, "compute_r2", "float"),),
    )

    migrate_script.apply_targets()
    migrated = target.read_text(encoding="utf-8")
    assert migrate_script.MARKER in migrated
    compile(migrated, str(target), "exec")

    # Re-running is idempotent.
    migrate_script.apply_targets()
    assert target.read_text(encoding="utf-8") == migrated


def test_migrate_baseline_writer_uses_only_temporary_tree(migrate_script, tmp_path, monkeypatch):
    package = tmp_path / "hypatiax"
    package.mkdir()
    (package / "legacy.py").write_text("total = ss_tot\n", encoding="utf-8")
    (package / "r2_canonical.py").write_text("ss_tot = 1\n", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    monkeypatch.setattr(migrate_script, "ROOT", tmp_path)
    monkeypatch.setattr(migrate_script, "BASELINE", baseline)

    migrate_script.write_baseline()

    import json

    payload = json.loads(baseline.read_text(encoding="utf-8"))
    assert payload["files"] == ["hypatiax/legacy.py"]
