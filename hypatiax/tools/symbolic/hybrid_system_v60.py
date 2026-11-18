"""Opt-in HybridDiscovery V60 migration boundary.

V60 validates an explicit immutable problem contract and generates a bounded,
data-independent native template proposal pool. Candidate fitting, external
LLM/PySR production, validation, and selection remain on the V50.2 baseline.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

import numpy as np

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryProblem, discovery_problem_from_dict
from hypatiax.tools.symbolic.hybrid_system_v50_2 import HybridDiscoverySystem\nfrom hypatiax.tools.symbolic.v60_candidate_generation import generate_native_template_candidates


@dataclass(frozen=True)
class V60RunContext:
    """Immutable, data-free identity and shape record for one discovery call."""
    contract_digest: str
    target_name: str
    variable_names: tuple[str, ...]
    domain: str
    training_shape: tuple[int, int]
    target_shape: tuple[int, ...]
    training_row_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_digest": self.contract_digest,
            "target_name": self.target_name,
            "variable_names": list(self.variable_names),
            "domain": self.domain,
            "training_shape": list(self.training_shape),
            "target_shape": list(self.target_shape),
            "training_row_count": self.training_row_count,
        }


def _prepare_v60_contract_context(X: Any, y: Any, var_names: list[str],
                                  metadata: Mapping[str, Any] | None,
                                  fallback_domain: str
                                  ) -> tuple[dict[str, Any], V60RunContext | None]:
    """Validate a supplied typed contract without copying or retaining data."""
    prepared = dict(metadata or {})
    problem = prepared.get("discovery_problem")
    spec = prepared.get("discovery_problem_spec")
    if problem is not None and spec is not None:
        raise ValueError("provide only discovery_problem or discovery_problem_spec")
    if spec is not None:
        problem = discovery_problem_from_dict(spec)
        prepared["discovery_problem"] = problem
    if problem is None:
        return prepared, None
    if not isinstance(problem, DiscoveryProblem):
        raise TypeError("discovery_problem must be a DiscoveryProblem or use a strict discovery_problem_spec mapping")

    names = tuple(var_names)
    if names != problem.variable_names:
        raise ValueError("problem contract variable_names must exactly match discovery input order")
    features, targets = np.asarray(X), np.asarray(y)
    if features.ndim != 2:
        raise ValueError(f"training features must be 2-D; got shape {features.shape}")
    if features.shape[1] != len(names):
        raise ValueError("training feature width does not match variable_names")
    if targets.ndim not in (1, 2) or targets.size != features.shape[0]:
        raise ValueError("training target must contain exactly one target per feature row")

    canonical = json.dumps(problem.to_dict(), sort_keys=True, separators=(",", ":"))
    context = V60RunContext(
        contract_digest=sha256(canonical.encode("utf-8")).hexdigest(),
        target_name=problem.target_name,
        variable_names=names,
        domain=problem.domain or fallback_domain,
        training_shape=(int(features.shape[0]), int(features.shape[1])),
        target_shape=tuple(int(size) for size in targets.shape),
        training_row_count=int(features.shape[0]),
    )
    return prepared, context


class HybridDiscoverySystemV60(HybridDiscoverySystem):
    """V60 contract-preflight stage with V50.2 candidate discovery baseline."""
    VERSION = "6.0.0"
    IMPLEMENTATION_MODE = "native_contract_preflight_v50_2_discovery"
    NATIVE_STAGES = ("typed_problem_contract_and_immutable_run_context",)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._last_v60_run_context: V60RunContext | None = None\n        self._last_v60_candidate_proposals: tuple[dict[str, Any], ...] = ()

    def _annotate_v60_result(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return result
        annotated = dict(result)
        provenance = annotated.get("implementation_provenance")
        provenance = dict(provenance) if isinstance(provenance, dict) else {}
        provenance.update({
            "engine_family": "hybrid_discovery",
            "engine_version": self.VERSION,
            "implementation_mode": self.IMPLEMENTATION_MODE,
            "native_v60_pipeline": False,
            "native_v60_stages": list(self.NATIVE_STAGES),
            "native_v60_contract_preflight": self._last_v60_run_context is not None,\n            "native_v60_candidate_generation": bool(self._last_v60_candidate_proposals),\n            "native_v60_candidate_count": len(self._last_v60_candidate_proposals),\n            "native_v60_candidate_ids": [item["candidate_id"] for item in self._last_v60_candidate_proposals],
            "v60_run_context": self._last_v60_run_context.to_dict() if self._last_v60_run_context else None,
            "compatibility_baseline": "hybrid_system_v50_2",
        })
        annotated["native_v60_candidate_proposals"] = [\n            dict(item) for item in self._last_v60_candidate_proposals\n        ]\n        annotated["implementation_provenance"] = provenance
        return annotated

    def discover(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Run native contract preflight, then the V50.2 compatibility pipeline."""
        if args:
            if len(args) < 3:
                raise TypeError("discover requires X, y, and var_names")
            X, y, var_names = args[:3]
            metadata = args[4] if len(args) > 4 else kwargs.get("metadata")
            description = args[3] if len(args) > 3 else kwargs.get("description", "")
            forwarded = list(args)
        else:
            try:
                X, y, var_names = kwargs["X"], kwargs["y"], kwargs["var_names"]
            except KeyError as exc:
                raise TypeError("discover requires X, y, and var_names") from exc
            metadata = kwargs.get("metadata")
            description = kwargs.get("description", "")
            forwarded = None

        prepared, self._last_v60_run_context = _prepare_v60_contract_context(
            X, y, var_names, metadata, self.domain
        )
        if forwarded is not None:
            if len(forwarded) > 4:
                forwarded[4] = prepared
            elif len(forwarded) == 4:
                forwarded.append(prepared)
            else:
                forwarded.extend([description, prepared])
            result = super().discover(*forwarded, **{
                key: value for key, value in kwargs.items() if key not in {"metadata", "description"}
            })
        else:
            call_kwargs = dict(kwargs)
            call_kwargs["metadata"] = prepared
            result = super().discover(**call_kwargs)
        return self._annotate_v60_result(result)

    def discover_validate_interpret(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Preserve the legacy entry point while exposing V60 provenance."""
        return self._annotate_v60_result(super().discover_validate_interpret(*args, **kwargs))
