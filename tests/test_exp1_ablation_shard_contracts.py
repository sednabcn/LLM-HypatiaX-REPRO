from pathlib import Path

import pytest

from hypatiax.experiments.benchmarks.exp1_ablation_contracts import (
    expected_equation_ids,
    formula_pathology_reasons,
    validate_shard_checkpoint,
)


def _completed(llm_called=False, success=True, timed_out=False):
    return {
        "completed": True,
        "llm_called": llm_called,
        "success": success,
        "timed_out": timed_out,
    }


def test_current_five_shards_cover_core15_exactly_once():
    shards = ("chemistry", "defi_risk", "biology", "physics", "defi_amm")
    assigned = [eq for slug in shards for eq in expected_equation_ids([slug])]
    assert sorted(assigned) == list(range(15))
    assert len(assigned) == len(set(assigned))


def test_shard_gate_ignores_unassigned_legacy_checkpoint_rows():
    checkpoint = {
        "0": {"name": "Arrhenius", "pysr_only": _completed(),
              "hypatia": _completed(llm_called=True),
              "hypatia_nollm": _completed()},
        # Legacy/master entries are not owned by the chemistry worker.
        "3": {"name": "Allometric Scaling"},
        "9": {"name": "Impermanent Loss"},
    }
    errors, warnings = validate_shard_checkpoint(
        checkpoint, ["chemistry"],
        ["pysr_only", "hypatia", "hypatia_nollm"],
    )
    assert errors == []
    assert warnings == []


def test_shard_gate_requires_all_arms_for_every_assigned_equation():
    checkpoint = {
        str(i): {
            "pysr_only": _completed(),
            "hypatia": _completed(llm_called=True),
            # Missing no-LLM arm must fail even if unrelated rows are complete.
        }
        for i in range(3)
    }
    errors, _ = validate_shard_checkpoint(
        checkpoint, ["chemistry"],
        ["pysr_only", "hypatia", "hypatia_nollm"],
    )
    assert len(errors) == 3
    assert all("hypatia_nollm" in error for error in errors)


def test_failed_completed_arm_is_retained_as_negative_result_not_dropped():
    checkpoint = {
        str(i): {
            "pysr_only": _completed(success=False),
            "hypatia": _completed(llm_called=True, success=False),
            "hypatia_nollm": _completed(success=False),
        }
        for i in range(3)
    }
    errors, warnings = validate_shard_checkpoint(
        checkpoint, ["chemistry"],
        ["pysr_only", "hypatia", "hypatia_nollm"],
    )
    assert errors == []
    assert len(warnings) == 3


def test_no_llm_arm_contamination_is_still_an_error():
    checkpoint = {
        str(i): {
            "pysr_only": _completed(),
            "hypatia": _completed(llm_called=True),
            "hypatia_nollm": _completed(llm_called=True),
        }
        for i in range(3)
    }
    errors, _ = validate_shard_checkpoint(
        checkpoint, ["chemistry"],
        ["pysr_only", "hypatia", "hypatia_nollm"],
    )
    assert all("hypatia_nollm made an LLM call" in error for error in errors)


def test_v3c_pathology_labels_are_diagnostic_only_and_stable():
    assert formula_pathology_reasons("x + nominal") == []
    assert formula_pathology_reasons("nan + np.inf + 1/0 + x**1000") == [
        "bare_nan_token",
        "literal_division_by_zero",
        "numpy_infinity_literal",
        "extreme_power_literal",
    ]


def test_exp1_protocol_contracts_remain_unchanged():
    source = (
        Path(__file__).parents[1]
        / "hypatiax/experiments/benchmarks/exp1_ablation.py"
    ).read_text(encoding="utf-8")
    # Existing arm names and per-equation seed schedule are intentionally unchanged.
    assert 'CONDITIONS         = ["pysr_only", "hypatia"] +' in source
    assert '["hypatia_nollm"] if os.environ.get("HYPATIAX_NOLLM_ARM") == "1"' in source
    assert 'eq_seed = seed + EQ_ID.get(eq["name"], 0) * 7' in source
    assert '"test_scope":            "untouched_outer_test"' in source
    assert 'generate_data(\n            eq, N=200, noise_level=0.05, seed=eq_seed' in source
    # v3c diagnostics must not become a gate or alter completed/success semantics.
    assert '"formula_pathology_reasons":' in source
    assert 'if formula_pathology_reasons(' not in source
