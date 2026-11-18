"""Versioned, serialisable contracts for physics-informed symbolic discovery.

These contracts describe scientific assumptions and audit evidence.  They do
not infer physical laws from variable names and deliberately keep evaluation
data out of the problem/selection interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
from types import MappingProxyType
from typing import Any, Mapping


CONTRACT_VERSION = "1.0"


def _freeze_value(value: Any) -> Any:
    """Recursively freeze nested contract containers."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_value(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Copy a mapping so callers cannot mutate a frozen contract indirectly."""
    return _freeze_value(dict(value or {}))


def _plain(value: Any) -> Any:
    """Convert contract values into deterministic JSON-compatible values."""
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if hasattr(value, "value"):
        return value.value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return str(value)


@dataclass(frozen=True)
class ConstraintSpec:
    """A declared scientific check; unknown assumptions stay undeclared."""

    constraint_id: str
    kind: str
    severity: str = "hard"
    source: str = "user_declared"
    parameters: Mapping[str, Any] = field(default_factory=dict)
    applicability: str = "declared_domain"
    description: str = ""

    def __post_init__(self) -> None:
        if not self.constraint_id.strip():
            raise ValueError("constraint_id must be non-empty")
        if not self.kind.strip():
            raise ValueError("constraint kind must be non-empty")
        if self.severity not in {"hard", "soft"}:
            raise ValueError("constraint severity must be 'hard' or 'soft'")
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))

    def to_dict(self) -> dict[str, Any]:
        return _plain({
            "constraint_id": self.constraint_id,
            "kind": self.kind,
            "severity": self.severity,
            "source": self.source,
            "parameters": self.parameters,
            "applicability": self.applicability,
            "description": self.description,
        })


@dataclass(frozen=True)
class DiscoveryBudget:
    """Explicit per-discovery resource ceilings; no implicit retry-to-LLM fanout."""

    max_search_attempts: int = 5
    max_candidates: int = 100
    max_llm_calls: int = 1
    max_llm_tokens: int | None = None
    max_wall_time_seconds: float | None = None
    seed: int = 42

    def __post_init__(self) -> None:
        for name in ("max_search_attempts", "max_candidates", "max_llm_calls"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")
        if self.max_llm_tokens is not None and self.max_llm_tokens < 0:
            raise ValueError("max_llm_tokens must be >= 0 or None")
        if self.max_wall_time_seconds is not None:
            if not math.isfinite(self.max_wall_time_seconds) or self.max_wall_time_seconds <= 0:
                raise ValueError("max_wall_time_seconds must be finite and > 0")

    def to_dict(self) -> dict[str, Any]:
        return _plain({
            "max_search_attempts": self.max_search_attempts,
            "max_candidates": self.max_candidates,
            "max_llm_calls": self.max_llm_calls,
            "max_llm_tokens": self.max_llm_tokens,
            "max_wall_time_seconds": self.max_wall_time_seconds,
            "seed": self.seed,
        })


@dataclass(frozen=True)
class DiscoveryProblem:
    """Immutable scientific contract for one equation-discovery task.

    Training observations and far-evaluation observations are intentionally
    not stored here.  Callers pass training data to discovery; far data belongs
    to a separate final-evaluation API and must never reach a selector.
    """

    target_name: str
    variable_names: tuple[str, ...]
    domain: str = "general"
    target_unit: str | None = None
    variable_units: Mapping[str, str] = field(default_factory=dict)
    variable_domains: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    constraints: tuple[ConstraintSpec, ...] = ()
    allowed_unary_operators: tuple[str, ...] = ()
    allowed_binary_operators: tuple[str, ...] = ()
    noise_model: str | None = None
    split_protocol: Mapping[str, Any] = field(default_factory=dict)
    budget: DiscoveryBudget = field(default_factory=DiscoveryBudget)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        names = tuple(self.variable_names)
        if not self.target_name.strip():
            raise ValueError("target_name must be non-empty")
        if not names or any(not str(name).strip() for name in names):
            raise ValueError("variable_names must contain non-empty names")
        if len(set(names)) != len(names):
            raise ValueError("variable_names must be unique")
        if not self.domain.strip():
            raise ValueError("domain must be non-empty")
        units = dict(self.variable_units or {})
        unknown_units = set(units) - set(names)
        if unknown_units:
            raise ValueError(f"variable_units contains unknown variables: {sorted(unknown_units)}")
        domains = {
            str(name): _freeze_mapping(spec)
            for name, spec in dict(self.variable_domains or {}).items()
        }
        unknown_domains = set(domains) - set(names)
        if unknown_domains:
            raise ValueError(
                f"variable_domains contains unknown variables: {sorted(unknown_domains)}"
            )
        constraint_ids = [item.constraint_id for item in self.constraints]
        if len(set(constraint_ids)) != len(constraint_ids):
            raise ValueError("constraint_id values must be unique")
        if not isinstance(self.budget, DiscoveryBudget):
            raise TypeError("budget must be a DiscoveryBudget")
        object.__setattr__(self, "variable_names", names)
        object.__setattr__(self, "variable_units", _freeze_mapping(units))
        object.__setattr__(self, "variable_domains", MappingProxyType(domains))
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "allowed_unary_operators", tuple(self.allowed_unary_operators))
        object.__setattr__(self, "allowed_binary_operators", tuple(self.allowed_binary_operators))
        object.__setattr__(self, "split_protocol", _freeze_mapping(self.split_protocol))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return _plain({
            "schema_version": self.schema_version,
            "target_name": self.target_name,
            "target_unit": self.target_unit,
            "variable_names": self.variable_names,
            "variable_units": self.variable_units,
            "variable_domains": self.variable_domains,
            "domain": self.domain,
            "constraints": [item.to_dict() for item in self.constraints],
            "allowed_unary_operators": self.allowed_unary_operators,
            "allowed_binary_operators": self.allowed_binary_operators,
            "noise_model": self.noise_model,
            "split_protocol": self.split_protocol,
            "budget": self.budget.to_dict(),
            "metadata": self.metadata,
        })



def _validate_json_value(value: Any, path: str) -> None:
    """Reject values that cannot cross a strict JSON worker boundary losslessly."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain only finite numbers")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} mapping keys must be strings")
            _validate_json_value(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    raise TypeError(f"{path} contains non-JSON value of type {type(value).__name__}")


def discovery_problem_from_dict(spec: Mapping[str, Any]) -> DiscoveryProblem:
    """Strictly deserialize a JSON-safe scientific contract at a worker boundary.

    This function validates types before constructing the immutable contract.
    It deliberately performs no string/number coercion and never infers physics.
    """
    if not isinstance(spec, Mapping):
        raise TypeError("discovery_problem_spec must be a mapping")
    _validate_json_value(spec, "discovery_problem_spec")
    allowed = {
        "schema_version", "target_name", "variable_names", "domain",
        "target_unit", "variable_units", "variable_domains", "constraints",
        "allowed_unary_operators", "allowed_binary_operators", "noise_model",
        "split_protocol", "budget", "metadata",
    }
    unknown = set(spec) - allowed
    if unknown:
        raise ValueError(f"unknown discovery problem fields: {sorted(unknown)}")
    if "target_name" not in spec or not isinstance(spec["target_name"], str):
        raise TypeError("discovery problem target_name must be a string")
    names_spec = spec.get("variable_names")
    if not isinstance(names_spec, (list, tuple)) or isinstance(names_spec, str):
        raise TypeError("discovery problem variable_names must be a list of strings")
    if any(not isinstance(name, str) for name in names_spec):
        raise TypeError("discovery problem variable_names must contain only strings")
    if "domain" in spec and not isinstance(spec["domain"], str):
        raise TypeError("discovery problem domain must be a string")
    for field_name in ("target_unit", "noise_model"):
        value = spec.get(field_name)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"discovery problem {field_name} must be a string or null")
    if "schema_version" in spec and not isinstance(spec["schema_version"], str):
        raise TypeError("discovery problem schema_version must be a string")
    version = spec.get("schema_version", CONTRACT_VERSION)
    if version != CONTRACT_VERSION:
        raise ValueError(f"unsupported discovery contract schema_version {version!r}")

    for field_name in ("variable_units", "variable_domains", "split_protocol", "metadata"):
        value = spec.get(field_name, {})
        if not isinstance(value, Mapping):
            raise TypeError(f"discovery problem {field_name} must be a mapping")
    if any(not isinstance(unit, str) for unit in spec.get("variable_units", {}).values()):
        raise TypeError("discovery problem variable_units values must be strings")
    if any(not isinstance(bounds, Mapping) for bounds in spec.get("variable_domains", {}).values()):
        raise TypeError("discovery problem variable_domains values must be mappings")
    for field_name in ("allowed_unary_operators", "allowed_binary_operators"):
        value = spec.get(field_name, ())
        if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
            raise TypeError(f"discovery problem {field_name} must be a list of strings")

    budget_spec = spec.get("budget", {})
    if not isinstance(budget_spec, Mapping):
        raise TypeError("discovery problem budget must be a mapping")
    budget_allowed = {
        "max_search_attempts", "max_candidates", "max_llm_calls",
        "max_llm_tokens", "max_wall_time_seconds", "seed",
    }
    budget_unknown = set(budget_spec) - budget_allowed
    if budget_unknown:
        raise ValueError(f"unknown discovery budget fields: {sorted(budget_unknown)}")
    for field_name in ("max_search_attempts", "max_candidates", "max_llm_calls", "seed"):
        if field_name in budget_spec and (
            isinstance(budget_spec[field_name], bool) or not isinstance(budget_spec[field_name], int)
        ):
            raise TypeError(f"discovery budget {field_name} must be an integer")
    if "max_llm_tokens" in budget_spec and budget_spec["max_llm_tokens"] is not None:
        value = budget_spec["max_llm_tokens"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("discovery budget max_llm_tokens must be an integer or null")
    if "max_wall_time_seconds" in budget_spec and budget_spec["max_wall_time_seconds"] is not None:
        value = budget_spec["max_wall_time_seconds"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("discovery budget max_wall_time_seconds must be numeric or null")

    constraints_spec = spec.get("constraints", ())
    if not isinstance(constraints_spec, (list, tuple)):
        raise TypeError("discovery problem constraints must be a list")
    constraints = []
    constraint_allowed = {
        "constraint_id", "kind", "severity", "source", "parameters",
        "applicability", "description",
    }
    for index, item in enumerate(constraints_spec):
        if not isinstance(item, Mapping):
            raise TypeError(f"constraint at index {index} must be a mapping")
        extra = set(item) - constraint_allowed
        if extra:
            raise ValueError(f"unknown constraint fields at index {index}: {sorted(extra)}")
        for field_name in ("constraint_id", "kind", "severity", "source", "applicability", "description"):
            if field_name in item and not isinstance(item[field_name], str):
                raise TypeError(f"constraint {field_name} at index {index} must be a string")
        if "parameters" in item and not isinstance(item["parameters"], Mapping):
            raise TypeError(f"constraint parameters at index {index} must be a mapping")
        constraints.append(ConstraintSpec(**dict(item)))

    return DiscoveryProblem(
        target_name=spec["target_name"],
        variable_names=tuple(names_spec),
        domain=spec.get("domain", "general"),
        target_unit=spec.get("target_unit"),
        variable_units=spec.get("variable_units", {}),
        variable_domains=spec.get("variable_domains", {}),
        constraints=tuple(constraints),
        allowed_unary_operators=tuple(spec.get("allowed_unary_operators", ())),
        allowed_binary_operators=tuple(spec.get("allowed_binary_operators", ())),
        noise_model=spec.get("noise_model"),
        split_protocol=spec.get("split_protocol", {}),
        budget=DiscoveryBudget(**dict(budget_spec)),
        metadata=spec.get("metadata", {}),
        schema_version=version,
    )


CONSTRAINT_STATUSES = frozenset({
    "pass", "fail", "warning", "not_applicable", "unknown", "not_checked"
})


@dataclass(frozen=True)
class ConstraintOutcome:
    """Inspectable result for one declared constraint."""

    constraint_id: str
    status: str
    severity: str = "hard"
    reason: str = ""
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in CONSTRAINT_STATUSES:
            raise ValueError(f"unsupported constraint status: {self.status}")
        if self.severity not in {"hard", "soft"}:
            raise ValueError("severity must be 'hard' or 'soft'")
        object.__setattr__(self, "evidence", _freeze_mapping(self.evidence))

    def to_dict(self) -> dict[str, Any]:
        return _plain({
            "constraint_id": self.constraint_id,
            "status": self.status,
            "severity": self.severity,
            "reason": self.reason,
            "evidence": self.evidence,
        })


@dataclass(frozen=True)
class CandidateRecord:
    """Auditable symbolic candidate with source, strategy, and gate outcomes."""

    expression: str
    source: str
    search_strategy: str
    seed: int
    normalized_expression: str | None = None
    candidate_id: str = ""
    constraint_outcomes: tuple[ConstraintOutcome, ...] = ()
    metrics: Mapping[str, Any] = field(default_factory=dict)
    rejection_reasons: tuple[str, ...] = ()
    eligible: bool = False

    def __post_init__(self) -> None:
        if not self.expression.strip():
            raise ValueError("candidate expression must be non-empty")
        if self.source not in {
            "llm_proposal", "domain_template", "pysr_search", "residual_search", "unknown"
        }:
            raise ValueError(f"unsupported candidate source: {self.source}")
        if not self.search_strategy.strip():
            raise ValueError("search_strategy must be non-empty")
        normalized = (self.normalized_expression or self.expression).strip()
        identity = {
            "expression": normalized,
            "source": self.source,
            "strategy": self.search_strategy,
            "seed": int(self.seed),
        }
        digest = sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()[:20]
        if self.candidate_id and self.candidate_id != digest:
            raise ValueError("candidate_id does not match candidate identity")
        object.__setattr__(self, "normalized_expression", normalized)
        object.__setattr__(self, "candidate_id", digest)
        object.__setattr__(self, "constraint_outcomes", tuple(self.constraint_outcomes))
        object.__setattr__(self, "metrics", _freeze_mapping(self.metrics))
        object.__setattr__(self, "rejection_reasons", tuple(self.rejection_reasons))

    def to_dict(self) -> dict[str, Any]:
        return _plain({
            "candidate_id": self.candidate_id,
            "expression": self.expression,
            "normalized_expression": self.normalized_expression,
            "source": self.source,
            "search_strategy": self.search_strategy,
            "seed": self.seed,
            "constraint_outcomes": [item.to_dict() for item in self.constraint_outcomes],
            "metrics": self.metrics,
            "rejection_reasons": self.rejection_reasons,
            "eligible": self.eligible,
        })


DISCOVERY_STATUSES = frozenset({
    "accepted", "provisional", "no_credible_candidate",
    "invalid_problem_specification", "no_candidates_generated",
    "all_candidates_failed_symbolic_validation",
    "all_candidates_failed_physical_gates",
    "insufficient_validation_evidence", "search_budget_exhausted",
    "llm_unavailable_fallback_used", "accepted_with_warnings",
})


@dataclass(frozen=True)
class DiscoveryReport:
    """Versioned result envelope; far metrics are segregated from selection."""

    status: str
    candidates: tuple[CandidateRecord, ...] = ()
    selected_candidate_id: str | None = None
    pareto_candidate_ids: tuple[str, ...] = ()
    failure_reasons: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    far_evaluation: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.status not in DISCOVERY_STATUSES:
            raise ValueError(f"unsupported discovery status: {self.status}")
        candidates = tuple(self.candidates)
        ids = [item.candidate_id for item in candidates]
        if len(set(ids)) != len(ids):
            raise ValueError("candidate IDs in a report must be unique")
        if self.selected_candidate_id is not None and self.selected_candidate_id not in ids:
            raise ValueError("selected_candidate_id must identify a report candidate")
        if self.selected_candidate_id is not None and self.status in {
            "no_credible_candidate", "invalid_problem_specification",
            "no_candidates_generated", "all_candidates_failed_symbolic_validation",
            "all_candidates_failed_physical_gates", "insufficient_validation_evidence",
            "search_budget_exhausted",
        }:
            raise ValueError("failure status cannot carry a selected candidate")
        if not set(self.pareto_candidate_ids).issubset(set(ids)):
            raise ValueError("pareto_candidate_ids must identify report candidates")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "pareto_candidate_ids", tuple(self.pareto_candidate_ids))
        object.__setattr__(self, "failure_reasons", tuple(self.failure_reasons))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "far_evaluation", _freeze_mapping(self.far_evaluation))

    def to_dict(self) -> dict[str, Any]:
        return _plain({
            "schema_version": self.schema_version,
            "status": self.status,
            "selected_candidate_id": self.selected_candidate_id,
            "pareto_candidate_ids": self.pareto_candidate_ids,
            "candidates": [item.to_dict() for item in self.candidates],
            "failure_reasons": self.failure_reasons,
            "provenance": self.provenance,
            "far_evaluation": self.far_evaluation,
            "far_evaluation_used_for_selection": False,
        })


__all__ = [
    "CONTRACT_VERSION",
    "ConstraintSpec",
    "DiscoveryBudget",
    "DiscoveryProblem",
    "discovery_problem_from_dict",
    "ConstraintOutcome",
    "CandidateRecord",
    "DiscoveryReport",
    "CONSTRAINT_STATUSES",
    "DISCOVERY_STATUSES",
]
