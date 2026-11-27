"""Regression tests for the scientific failure modes found in Core-15."""
from hypatiax.experiments.benchmarks.exp1_ablation_contracts import (
    audit_core15_expression,
    build_core15_discovery_problem,
)
from hypatiax.tools.symbolic.discovery_validation import CandidateValidator


def _problem(name, variables, ranges):
    return build_core15_discovery_problem(
        {
            "name": name,
            "domain": "Physics",
            "vars": variables,
            "train_range": ranges,
        },
        variables,
        seed=777,
    )


def _validate(problem, expression):
    return CandidateValidator().validate(problem, expression, source="pysr_search")


def _reasons(record):
    return " ".join(record.rejection_reasons).lower()


def test_ideal_gas_candidate_cannot_omit_temperature_and_volume():
    problem = _problem(
        "Ideal Gas Law", ["n", "T", "V"],
        [(0.1, 5.0), (200.0, 500.0), (0.01, 1.0)],
    )
    bad = _validate(problem, "sqrt(n * 5.4327)")
    good = _validate(problem, "n * T / V")
    negative = _validate(problem, "-n*T/V")
    assert not bad.eligible
    assert "missing" in _reasons(bad)
    assert "'T'" in _reasons(bad) and "'V'" in _reasons(bad)
    assert good.eligible
    assert not negative.eligible


def test_arrhenius_requires_exponential_reciprocal_temperature_and_no_nesting():
    problem = _problem("Arrhenius", ["T"], [(300.0, 500.0)])
    wrong_power_law = _validate(problem, "(T / 434.6)**12.9")
    nested_exponential = _validate(problem, "exp(exp(413.0 / T))")
    correct_family = _validate(problem, "1.0e6 * exp(-50000.0 / (8.314 * T))")
    assert not wrong_power_law.eligible
    assert not nested_exponential.eligible
    assert correct_family.eligible


def test_impermanent_loss_requires_square_root_and_reciprocal_symmetry():
    problem = _problem("Impermanent Loss", ["r"], [(0.5, 2.0)])
    wrong_linear_inverse_fit = _validate(problem, "-11.67*r - 11.68/r + 23.33")
    correct_family = _validate(problem, "2*sqrt(r)/(1+r)-1")
    positive_shift = _validate(problem, "2*sqrt(r)/(1+r)")
    assert not wrong_linear_inverse_fit.eligible
    assert not positive_shift.eligible
    assert correct_family.eligible


def test_kinetic_energy_rejects_logarithmic_and_wrong_velocity_dependence():
    problem = _problem(
        "Kinetic Energy", ["m", "v"],
        [(0.5, 10.0), (1.0, 20.0)],
    )
    bad = _validate(
        problem,
        "log(v*sqrt(m)*0.51 - 0.87 - 0.046/(m-2.069))",
    )
    good = _validate(problem, "0.5*m*v**2")
    near_canonical = _validate(problem, "0.52*m*v**1.985")
    assert not bad.eligible
    assert "forbidden" in _reasons(bad) or "required" in _reasons(bad)
    assert good.eligible
    assert near_canonical.eligible


def test_gravity_rejects_variable_exponents_and_requires_inverse_square_distance():
    problem = _problem(
        "Gravitational Force", ["m1", "m2", "r"],
        [(1e10, 1e12), (1e10, 1e12), (1e6, 1e8)],
    )
    bad = _validate(problem, "log(m1*m2/r)**(1.5**r)")
    wrong_mass_power = _validate(problem, "0.036*m1**0.25*m2/r**2")
    good = _validate(problem, "6.674e-11*m1*m2/r**2")
    physical_constant_form = _validate(problem, "G*m1*m2/r**2")
    assert not bad.eligible
    assert not wrong_mass_power.eligible
    assert good.eligible
    assert physical_constant_form.eligible


def test_logistic_growth_requires_quadratic_population_term():
    problem = _problem("Logistic Growth", ["N"], [(10.0, 500.0)])
    bad = _validate(problem, "0.3*N")
    good = _validate(problem, "0.3*N*(1-N/1000)")
    assert not bad.eligible
    assert good.eligible


def test_core15_contract_contains_no_held_out_or_far_target_values():
    problem = _problem("Ideal Gas Law", ["n", "T", "V"], [
        (0.1, 5.0), (200.0, 500.0), (0.01, 1.0)
    ])
    payload = problem.to_dict()
    assert payload["split_protocol"]["training_domain_only"] is True
    assert payload["split_protocol"]["held_out_targets_available_to_selector"] is False
    assert payload["split_protocol"]["far_ood_target_data_available_to_selector"] is False
    assert "test_y" not in payload and "far_y" not in payload


def test_post_selection_audit_marks_pySR_style_failures_without_rewriting_metrics():
    equation = {
        "name": "Ideal Gas Law",
        "domain": "Physics",
        "vars": ["n", "T", "V"],
        "train_range": [(0.1, 5.0), (200.0, 500.0), (0.01, 1.0)],
    }
    audit = audit_core15_expression(equation, "sqrt(n*5.4327)", seed=777)
    assert audit["eligible"] is False
    assert audit["source"] == "unknown"
    assert audit["search_strategy"] == "audit_only"
    assert audit["rejection_reasons"]


def test_michaelis_menten_requires_saturating_denominator_and_shape():
    problem = _problem("Michaelis-Menten", ["S"], [(0.1, 5.0)])
    bad = _validate(problem, "2*S")
    good = _validate(problem, "10*S/(2+S)")
    assert not bad.eligible
    assert good.eligible


def test_logistic_candidate_must_be_increasing_and_concave_on_training_domain():
    problem = _problem("Logistic Growth", ["N"], [(10.0, 500.0)])
    convex = _validate(problem, "0.3*N + 0.0001*N**2")
    logistic = _validate(problem, "0.3*N*(1-N/1000)")
    assert not convex.eligible
    assert logistic.eligible


def test_ideal_gas_contract_accepts_declared_physical_constants():
    problem = _problem(
        "Ideal Gas Law", ["n", "T", "V"],
        [(0.1, 5.0), (200.0, 500.0), (0.01, 1.0)],
    )
    record = _validate(problem, "n * T * k_B * N_A / V")
    gas_constant_form = _validate(problem, "n * R * T / V")
    assert record.eligible
    assert gas_constant_form.eligible
