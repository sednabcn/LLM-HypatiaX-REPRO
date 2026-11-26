"""Stable contracts shared by Exp1 ablation shard gates and regression tests.

This module deliberately validates *assigned* Core-15 equations at worker scope.
The aggregate gate remains responsible for validating the complete 0..14 registry.
"""
from __future__ import annotations

import re
from typing import Iterable

CORE15_SHARD_EQUATION_IDS = {
    "chemistry": (0, 1, 2),
    "biology": (3, 4, 5),
    "physics": (6, 7, 8),
    "defi_amm": (9, 10, 11),
    "defi_risk": (12, 13, 14),
}

# Backwards-compatible aliases accepted by exp1_ablation.py's shard filter.
CORE15_SHARD_EQUATION_IDS.update({
    "amm": (9, 10, 11),
    "liquidity": (9, 10, 11),
    "risk_var": (12,),
    "expected_shortfall": (12,),
    "liquidation": (13,),
    "risk": (14,),
    "lending": (),
    "staking": (),
    "trading": (),
    "derivatives": (),
})


def expected_equation_ids(task_ids: Iterable[str]) -> tuple[int, ...]:
    """Resolve workflow task slugs to stable global Core-15 equation IDs."""
    ids = []
    unknown = []
    for raw in task_ids:
        slug = str(raw).strip().lower()
        if not slug:
            continue
        if slug not in CORE15_SHARD_EQUATION_IDS:
            unknown.append(slug)
            continue
        ids.extend(CORE15_SHARD_EQUATION_IDS[slug])
    if unknown:
        raise ValueError(f"unknown Exp1 ablation shard task ID(s): {sorted(set(unknown))}")
    return tuple(sorted(set(ids)))


def validate_shard_checkpoint(
    checkpoint: dict,
    task_ids: Iterable[str],
    arms: Iterable[str],
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for only this shard's assigned equations.

    A completed arm may legitimately contain a failed model outcome or timeout:
    completion records the attempt; success records its scientific outcome.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(checkpoint, dict):
        return ["checkpoint root must be a JSON object"], warnings
    assigned = expected_equation_ids(task_ids)
    if not assigned:
        return ["shard task IDs resolve to no Core-15 equations"], warnings

    arm_names = tuple(arms)
    for eq_id in assigned:
        key = str(eq_id)
        row = checkpoint.get(key)
        if not isinstance(row, dict):
            errors.append(f"equation {key}: missing assigned equation record")
            continue
        missing = [
            arm for arm in arm_names
            if not isinstance(row.get(arm), dict)
            or row[arm].get("completed") is not True
        ]
        if missing:
            errors.append(f"equation {key}: missing/incomplete arm(s) {missing}")
            continue

        hypatia = row.get("hypatia") or {}
        nollm = row.get("hypatia_nollm") or {}
        if "hypatia_nollm" in arm_names and nollm.get("llm_called") is True:
            errors.append(f"equation {key}: hypatia_nollm made an LLM call")
        elif "hypatia_nollm" in arm_names and nollm.get("llm_called") is None:
            warnings.append(f"equation {key}: no llm_called flag on hypatia_nollm; LLM-free status is unproven")
        if "hypatia" in arm_names and hypatia.get("llm_called") is not True:
            if hypatia.get("timed_out"):
                warnings.append(f"equation {key}: hypatia timed out before a live LLM call")
            else:
                errors.append(
                    f"equation {key}: hypatia has no evidence of a live LLM call "
                    f"(llm_called={hypatia.get('llm_called')!r})"
                )
        elif "hypatia" in arm_names and hypatia.get("success") is False:
            warnings.append(
                f"equation {key}: hypatia failed after a live LLM call; retained as a negative result"
            )
    return errors, warnings


def formula_pathology_reasons(code: str | None) -> list[str]:
    """v3c-style, non-operative formula pathology diagnostics for Exp1 records.

    These labels are annotations only: they never reject a candidate, change a
    predictor, affect model selection, or alter the ablation's result accounting.
    """
    if not isinstance(code, str) or not code.strip():
        return []
    reasons = []
    if re.search(r"\bnan\b", code):
        reasons.append("bare_nan_token")
    low = code.lower()
    for pattern, reason in (
        ("1/0", "literal_division_by_zero"),
        ("np.inf", "numpy_infinity_literal"),
        ("**1000", "extreme_power_literal"),
    ):
        if pattern in low:
            reasons.append(reason)
    return reasons
