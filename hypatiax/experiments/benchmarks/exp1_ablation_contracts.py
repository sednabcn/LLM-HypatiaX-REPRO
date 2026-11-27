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


def build_core15_discovery_problem(
    equation: dict,
    safe_variable_names: Iterable[str],
    seed: int,
):
    """Build an explicit, label-free scientific contract for one Core-15 task.

    The contract contains only declared input ranges and equation-structure
    requirements. It never receives train/test/far target arrays or scores.
    Variable names are the sanitized names passed to the symbolic engine.
    """
    from hypatiax.tools.symbolic.discovery_contracts import (
        ConstraintSpec,
        DiscoveryBudget,
        DiscoveryProblem,
    )

    names = tuple(str(name) for name in safe_variable_names)
    original_names = tuple(str(name) for name in equation.get("vars", ()))
    train_ranges = tuple(equation.get("train_range", ()))
    if not names or len(names) != len(original_names) or len(train_ranges) != len(names):
        raise ValueError("Core-15 contract requires aligned variables and training ranges")

    domains = {}
    for safe_name, bounds in zip(names, train_ranges):
        if len(bounds) != 2:
            raise ValueError(f"invalid training range for {safe_name}")
        low, high = float(bounds[0]), float(bounds[1])
        if not (low < high):
            raise ValueError(f"invalid training range for {safe_name}: {(low, high)}")
        domains[safe_name] = {"minimum": low, "maximum": high}

    constraints = [
        ConstraintSpec(
            "core15.required_variables",
            "required_variables",
            severity="hard",
            source="core15_benchmark_contract",
            parameters={"variables": list(names)},
            description="Every declared independent input must occur in the selected expression.",
        ),
        ConstraintSpec(
            "core15.finite_training_domain",
            "finite_output_screen",
            severity="hard",
            source="core15_benchmark_contract",
            description="Expression must remain finite on a deterministic grid over the declared training domain.",
        ),
    ]

    def add(kind, suffix, parameters=None, description=""):
        constraints.append(ConstraintSpec(
            f"core15.{suffix}",
            kind,
            severity="hard",
            source="core15_benchmark_contract",
            parameters=parameters or {},
            description=description,
        ))

    equation_name = str(equation.get("name", "")).strip().lower()
    safe_by_original = dict(zip(original_names, names))
    if equation_name == "impermanent loss":
        add("nonpositive_output_screen", "impermanent_loss_nonpositive",
            description="Impermanent loss is non-positive relative to the hold benchmark.")
    else:
        add("positive_output_screen", "core15_positive_output",
            description="This Core-15 target family is positive over its declared training domain.")

    if equation_name == "arrhenius":
        add("required_functions", "arrhenius_exponential", {"functions": ["exp"]},
            "Arrhenius kinetics requires exponential dependence.")
        add("required_inverse_inside_function", "arrhenius_reciprocal_temperature",
            {"function": "exp", "variable": safe_by_original["T"]},
            "The exponential argument must depend on reciprocal absolute temperature.")
        add("no_nested_functions", "arrhenius_no_nested_exponential", {"functions": ["exp"]},
            "Nested exponentials are not part of the declared Arrhenius family.")
    elif equation_name == "impermanent loss":
        add("required_power", "impermanent_loss_square_root",
            {"variable": safe_by_original["r"], "exponent": 0.5},
            "The constant-product impermanent-loss family contains a square-root price-ratio term.")
        add("reciprocal_even_in", "impermanent_loss_reciprocal_symmetry",
            {"variable": safe_by_original["r"]},
            "Impermanent loss is invariant under reciprocal price-ratio transformation.")
    elif equation_name == "ideal gas law":
        add("required_power", "ideal_gas_mole_linearity",
            {"variable": safe_by_original["n"], "exponent": 1.0},
            "The ideal-gas law is linear in amount of substance.")
        add("required_power", "ideal_gas_temperature_linearity",
            {"variable": safe_by_original["T"], "exponent": 1.0},
            "The ideal-gas law is linear in absolute temperature.")
        add("required_power", "ideal_gas_inverse_volume",
            {"variable": safe_by_original["V"], "exponent": -1.0},
            "The ideal-gas law is inverse in volume.")
        add("no_variable_exponents", "ideal_gas_constant_exponents",
            description="Ideal-gas exponents are fixed, not input-dependent.")
    elif equation_name == "michaelis-menten":
        add("variable_in_denominator", "michaelis_menten_saturation_denominator",
            {"variable": safe_by_original["S"]},
            "Michaelis-Menten kinetics has substrate concentration in its saturation denominator.")
        add("monotone_concave_in", "michaelis_menten_saturating_shape",
            {"variable": safe_by_original["S"]},
            "The Michaelis-Menten rate is increasing and concave-down over the declared substrate domain.")
    elif equation_name == "kinetic energy":
        add("required_power", "kinetic_energy_mass_linearity",
            {"variable": safe_by_original["m"], "exponent": 1.0},
            "Classical kinetic energy is linear in mass.")
        add("required_power", "kinetic_energy_velocity_squared",
            {"variable": safe_by_original["v"], "exponent": 2.0, "tolerance": 0.05},
            "Classical kinetic energy is quadratic in velocity.")
        add("forbidden_functions", "kinetic_energy_no_log", {"functions": ["log", "log10"]},
            "A logarithmic transform is not part of the declared kinetic-energy law.")
        add("no_variable_exponents", "kinetic_energy_constant_exponents",
            description="The physical power-law exponents are constants, not input-dependent.")
    elif equation_name == "gravitational force":
        add("required_power", "gravity_linear_mass_1",
            {"variable": safe_by_original["m1"], "exponent": 1.0},
            "Newtonian gravity is linear in the first mass.")
        add("required_power", "gravity_linear_mass_2",
            {"variable": safe_by_original["m2"], "exponent": 1.0},
            "Newtonian gravity is linear in the second mass.")
        add("required_power", "gravity_inverse_square_distance",
            {"variable": safe_by_original["r"], "exponent": -2.0},
            "Newtonian gravity has inverse-square distance dependence.")
        add("forbidden_functions", "gravity_no_log", {"functions": ["log", "log10"]},
            "Logarithmic transforms are not part of the declared Newtonian force law.")
        add("no_variable_exponents", "gravity_constant_exponents",
            description="Newtonian mass and distance exponents are constants.")
    elif equation_name == "logistic growth":
        add("required_power", "logistic_quadratic_population",
            {"variable": safe_by_original["N"], "exponent": 2.0},
            "The logistic growth law contains a quadratic population term.")
        add("monotone_concave_in", "logistic_training_domain_shape",
            {"variable": safe_by_original["N"]},
            "On the declared pre-carrying-capacity training interval, logistic growth is increasing and concave-down.")

    return DiscoveryProblem(
        target_name=str(equation.get("name", "Core-15 target")),
        variable_names=names,
        domain=str(equation.get("domain", "general")).lower().replace(" ", "_"),
        variable_domains=domains,
        constraints=tuple(constraints),
        split_protocol={
            "training_domain_only": True,
            "held_out_targets_available_to_selector": False,
            "far_ood_target_data_available_to_selector": False,
        },
        budget=DiscoveryBudget(
            max_search_attempts=3,
            max_candidates=100,
            max_llm_calls=1,
            seed=int(seed),
        ),
        metadata={
            "contract_family": "exp1_core15",
            "contract_version": 1,
            "equation_name": str(equation.get("name", "")),
            "original_variable_names": list(original_names),
            "safe_variable_names": list(names),
            "scientific_priors_are_declared": True,
        },
    )


def audit_core15_expression(equation: dict, expression: str, seed: int) -> dict:
    """Return a post-selection scientific audit without changing benchmark metrics."""
    from hypatiax.tools.symbolic.discovery_validation import CandidateValidator

    problem = build_core15_discovery_problem(
        equation, equation.get("vars", ()), seed
    )
    return CandidateValidator().validate(
        problem,
        expression,
        source="unknown",
        search_strategy="audit_only",
        seed=seed,
    ).to_dict()
