"""Opt-in HybridDiscovery V60 native training orchestration.

Explicit activation requires a typed immutable problem contract and connects
bounded proposal ingestion, scientific gates, training-fold validation,
verified single-/multi-basis selection, finalization, and a separate frozen
far-evaluation API. The default path remains V50.2 compatible.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

import numpy as np

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryProblem, discovery_problem_from_dict
from hypatiax.tools.symbolic.discovery_report_integrity import build_native_discovery_report
from hypatiax.tools.symbolic.hybrid_system_v50_2 import HybridDiscoverySystem
from hypatiax.tools.symbolic.v60_candidate_generation import generate_native_template_candidates
from hypatiax.tools.symbolic.v60_external_producers import ingest_external_candidate_proposals
from hypatiax.tools.symbolic.v60_candidate_normalization import normalize_candidate_proposals
from hypatiax.tools.symbolic.v60_candidate_fitting import fit_native_candidates
from hypatiax.tools.symbolic.v60_candidate_gating import validate_native_candidate_pool
from hypatiax.tools.symbolic.v60_training_validation import validate_native_training_candidates
from hypatiax.tools.symbolic.v60_multi_basis_fitting import fit_native_multi_basis_candidates
from hypatiax.tools.symbolic.v60_multi_basis_validation import validate_native_multi_basis_candidates
from hypatiax.tools.symbolic.v60_multi_basis_evidence import verify_native_multi_basis_validation_evidence
from hypatiax.tools.symbolic.v60_multi_basis_objective_selection import select_native_multi_basis_candidates_from_verified_evidence
from hypatiax.tools.symbolic.v60_objective_selection import select_native_candidates_from_training_evidence
from hypatiax.tools.symbolic.v60_residual_stability import diagnose_native_training_residuals
from hypatiax.tools.symbolic.v60_native_finalization import finalize_native_v60_model
from hypatiax.tools.symbolic.v60_production_handoff import (
    build_native_v60_result, evaluate_frozen_native_v60_model,
)


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
    """V60 native orchestration with V50.2 as the default compatibility path."""
    VERSION = "6.0.0"
    IMPLEMENTATION_MODE = "native_v60_training_selection_with_separate_frozen_far_evaluation"
    NATIVE_STAGES = (
        "typed_problem_contract_and_immutable_run_context",
        "bounded_data_independent_template_generation",
        "restricted_expression_normalization_semantic_identity_and_deduplication",
        "producer_lineage_preservation",
        "bounded_training_only_affine_candidate_fitting",
        "data_independent_scientific_candidate_gates",
        "training_only_single_basis_fold_validation",
        "training_only_multi_basis_joint_fitting_and_fold_validation",
        "independent_multi_basis_evidence_verification",
        "training_only_single_and_multi_basis_objective_selection",
        "training_only_residual_stability_diagnostics",
        "cross_family_finalization_and_frozen_model_audit",
        "separate_post_finalization_frozen_far_evaluation",
    )

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._last_v60_run_context: V60RunContext | None = None
        self._last_v60_candidate_proposals: tuple[dict[str, Any], ...] = ()
        self._last_v60_normalization_audit: dict[str, Any] = {}
        self._last_v60_fitting_audit: dict[str, Any] = {}

    def _reset_v60_call_state(self) -> None:
        """Clear every V60 audit before a new call to prevent cross-call leakage."""
        self._last_v60_run_context = None
        self._last_v60_candidate_proposals = ()
        self._last_v60_normalization_audit = {}
        self._last_v60_fitting_audit = {}
        self._last_v60_training_fit_audit = {}
        self._last_v60_multi_basis_fit_audit = {}
        self._last_v60_multi_basis_validation_audit = {}
        self._last_v60_multi_basis_evidence_audit = {}
        self._last_v60_multi_basis_selection_audit = {}
        self._last_v60_gate_audit = {}
        self._last_v60_training_validation_audit = {}
        self._last_v60_objective_selection_audit = {}
        self._last_v60_residual_stability_audit = {}
        self._last_v60_external_producer_audit = {}
        self._last_v60_final_model_audit = {}
        self._last_v60_far_evaluation_audit = {}
        self._last_v60_activate_native_result = False

    def _annotate_v60_result(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return result
        annotated = dict(result)
        provenance = annotated.get("implementation_provenance")
        provenance = dict(provenance) if isinstance(provenance, dict) else {}
        provenance.update({
            "engine_family": "hybrid_discovery",
            "engine_version": self.VERSION,
            "implementation_mode": (self.IMPLEMENTATION_MODE if self._last_v60_activate_native_result else "native_contract_generation_normalization_fitting_v50_2_discovery"),
            "native_v60_pipeline": bool(self._last_v60_activate_native_result and self._last_v60_final_model_audit.get("execution_status") == "selected"),
            "native_v60_production_handoff_enabled": self._last_v60_activate_native_result,
            "native_v60_far_evaluation_status": self._last_v60_far_evaluation_audit.get("evaluation_status", "not_requested"),
            "native_v60_far_evaluation_audit": dict(self._last_v60_far_evaluation_audit),
            "native_v60_stages": list(self.NATIVE_STAGES if self._last_v60_activate_native_result else self.NATIVE_STAGES[:5]),
            "native_v60_contract_preflight": self._last_v60_run_context is not None,
            "native_v60_candidate_generation": self._last_v60_run_context is not None,
            "native_v60_candidate_normalization": self._last_v60_run_context is not None,
            "native_v60_candidate_fitting": self._last_v60_run_context is not None,
            "native_v60_fitting_audit": dict(self._last_v60_fitting_audit),
            "native_v60_candidate_count": len(self._last_v60_candidate_proposals),
            "native_v60_external_producer_audit": dict(self._last_v60_external_producer_audit),
            "native_v60_normalization_audit": dict(self._last_v60_normalization_audit),
            "native_v60_candidate_ids": [item["candidate_id"] for item in self._last_v60_candidate_proposals],
            "v60_run_context": self._last_v60_run_context.to_dict() if self._last_v60_run_context else None,
            "compatibility_baseline": "hybrid_system_v50_2",
            "native_v60_gate_audit": dict(self._last_v60_gate_audit),
            "native_v60_training_validation_audit": dict(self._last_v60_training_validation_audit),
            "native_v60_multi_basis_fit_audit": dict(self._last_v60_multi_basis_fit_audit),
            "native_v60_multi_basis_validation_audit": dict(self._last_v60_multi_basis_validation_audit),
            "native_v60_multi_basis_evidence_audit": dict(self._last_v60_multi_basis_evidence_audit),
            "native_v60_objective_selection_audit": dict(self._last_v60_objective_selection_audit),
            "native_v60_multi_basis_selection_audit": dict(self._last_v60_multi_basis_selection_audit),
            "native_v60_residual_stability_audit": dict(self._last_v60_residual_stability_audit),
        })
        annotated["native_v60_candidate_proposals"] = [
            dict(item) for item in self._last_v60_candidate_proposals
        ]
        if self._last_v60_run_context is not None:
            try:
                annotated["discovery_report_envelope"] = build_native_discovery_report(
                    list(self._last_v60_candidate_proposals),
                    self._last_v60_gate_audit,
                    self._last_v60_training_validation_audit,
                    self._last_v60_objective_selection_audit,
                    run_context=self._last_v60_run_context.to_dict(),
                    multi_basis_selection_audit=self._last_v60_multi_basis_selection_audit,
                    final_model_audit=self._last_v60_final_model_audit,
                    far_evaluation_audit=self._last_v60_far_evaluation_audit,
                    residual_stability_audit=self._last_v60_residual_stability_audit,
                )
            except Exception as exc:
                annotated["discovery_report_error"] = f"{type(exc).__name__}: {exc}"
        if self._last_v60_final_model_audit:
            annotated["native_v60_final_model"] = dict(self._last_v60_final_model_audit)
        if self._last_v60_far_evaluation_audit:
            annotated["native_v60_far_evaluation"] = dict(self._last_v60_far_evaluation_audit)
        if self._last_v60_activate_native_result:
            if self._last_v60_final_model_audit.get("execution_status") == "selected":
                native = build_native_v60_result(self._last_v60_final_model_audit)
                annotated.update(native)
                annotated["v50_2_compatibility_result"] = {
                    "status": "not_executed",
                    "reason": "native_v60_production_handoff_enabled",
                }
                annotated["native_v60_production_handoff"] = {
                    "status": "active",
                    "selection_source": "verified_training_only_single_multi_basis_pareto",
                    "far_evaluation_attached": self._last_v60_far_evaluation_audit.get("evaluation_status") == "completed",
                }
            else:
                annotated.update({
                    "success": False,
                    "error": "NO_CREDIBLE_CANDIDATE",
                    "formula": "N/A",
                    "expression": "N/A",
                    "final_formula": "N/A",
                    "native_v60_production_handoff": {
                        "status": "blocked_no_credible_native_model",
                        "final_model_status": self._last_v60_final_model_audit.get("execution_status", "not_run"),
                    },
                })
        annotated["implementation_provenance"] = provenance
        return annotated

    def _run_native_v60_training_pipeline(
        self, X: Any, y: Any, problem: DiscoveryProblem,
        external_spec: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Run the complete native training-only pipeline; far data is not accepted."""
        generated = list(generate_native_template_candidates(problem))
        unknown_fields = set(external_spec) - {
            "llm_proposals", "pysr_proposals", "llm_call_count",
            "llm_token_count", "pysr_search_attempt_count",
        }
        if unknown_fields:
            raise ValueError(f"unknown external producer fields: {sorted(unknown_fields)}")
        external = ingest_external_candidate_proposals(
            problem,
            llm_proposals=external_spec.get("llm_proposals", ()),
            pysr_proposals=external_spec.get("pysr_proposals", ()),
            llm_call_count=external_spec.get("llm_call_count", 0),
            llm_token_count=external_spec.get("llm_token_count", 0),
            pysr_search_attempt_count=external_spec.get("pysr_search_attempt_count", 0),
        )
        cap = min(problem.budget.max_candidates, problem.budget.max_search_attempts)
        combined = (external["proposals"] + [item.to_dict() for item in generated])[:cap]
        self._last_v60_external_producer_audit = dict(external)
        normalized = normalize_candidate_proposals(
            combined, variable_names=problem.variable_names,
            max_candidates=problem.budget.max_candidates,
        )
        candidates = tuple(item.to_dict() for item in normalized.candidates)
        self._last_v60_candidate_proposals = candidates
        self._last_v60_normalization_audit = normalized.to_dict()
        self._last_v60_normalization_audit.pop("candidates", None)

        budget = problem.budget
        fitted = fit_native_candidates(
            candidates, X, y, variable_names=problem.variable_names,
            max_candidates=budget.max_candidates,
            max_search_attempts=budget.max_search_attempts,
            max_wall_time_seconds=budget.max_wall_time_seconds,
        )
        self._last_v60_fitting_audit = fitted.to_dict()

        gate = validate_native_candidate_pool(candidates, problem)
        self._last_v60_gate_audit = gate
        eligible_ids = [
            item["native_candidate_id"] for item in gate["candidate_gates"]
            if item.get("eligible") is True and item.get("gate_execution") == "completed"
        ]
        single_validation = validate_native_training_candidates(
            candidates, X, y, variable_names=problem.variable_names,
            eligible_candidate_ids=eligible_ids,
            split_protocol=problem.split_protocol, seed=budget.seed,
            max_candidates=budget.max_candidates,
            max_search_attempts=budget.max_search_attempts,
            max_wall_time_seconds=budget.max_wall_time_seconds,
        )
        self._last_v60_training_validation_audit = single_validation
        single_selection = select_native_candidates_from_training_evidence(
            candidates, gate, single_validation,
            variable_names=problem.variable_names,
            max_candidates=budget.max_candidates,
            max_search_attempts=budget.max_search_attempts,
        )
        self._last_v60_objective_selection_audit = single_selection

        eligible_candidates = [
            item for item in candidates if item.get("candidate_id") in set(eligible_ids)
        ]
        multi_fit = fit_native_multi_basis_candidates(
            eligible_candidates, X, y, variable_names=problem.variable_names,
            max_candidates=budget.max_candidates,
            max_search_attempts=budget.max_search_attempts,
            max_basis_terms=3,
            max_wall_time_seconds=budget.max_wall_time_seconds,
        )
        self._last_v60_multi_basis_fit_audit = multi_fit
        multi_validation = validate_native_multi_basis_candidates(
            multi_fit["fitted_candidate_groups"], eligible_candidates, X, y,
            variable_names=problem.variable_names,
            split_protocol=problem.split_protocol, seed=budget.seed,
            max_candidates=budget.max_candidates,
            max_search_attempts=budget.max_search_attempts,
            max_wall_time_seconds=budget.max_wall_time_seconds,
        )
        self._last_v60_multi_basis_validation_audit = multi_validation
        if multi_validation.get("validation_status") == "completed":
            multi_evidence = verify_native_multi_basis_validation_evidence(
                multi_validation, eligible_candidates, X, y,
                variable_names=problem.variable_names,
                max_groups=budget.max_candidates,
                max_search_attempts=budget.max_search_attempts,
            )
            multi_selection = select_native_multi_basis_candidates_from_verified_evidence(
                eligible_candidates, gate, multi_fit, multi_validation, multi_evidence,
                variable_names=problem.variable_names,
                max_groups=budget.max_candidates,
                max_search_attempts=budget.max_search_attempts,
            )
        else:
            multi_evidence = {
                "schema": "v60_native_multi_basis_evidence_verification_v1",
                "verification_status": "partial_or_rejected",
                "reason": "multi-basis training-fold validation did not complete",
                "selection_performed": False,
                "far_or_evaluation_data_used": False,
                "verified_candidate_groups": [],
                "rejected_candidate_groups": [],
            }
            multi_selection = {
                "schema": "v60_native_multi_basis_objective_selection_v1",
                "selection_status": "insufficient_validation_evidence",
                "reason": "multi-basis training-fold validation did not complete",
                "selection_performed": False,
                "far_or_evaluation_data_used": False,
                "objective_evidence": [],
                "pareto_candidate_group_ids": [],
                "selected_candidate_group_id": None,
            }
        self._last_v60_multi_basis_evidence_audit = multi_evidence
        self._last_v60_multi_basis_selection_audit = multi_selection

        self._last_v60_residual_stability_audit = diagnose_native_training_residuals(
            candidates, single_validation, X, y,
            variable_names=problem.variable_names,
            max_candidates=budget.max_candidates,
            max_search_attempts=budget.max_search_attempts,
        )
        final_audit = finalize_native_v60_model(
            candidates, single_selection, multi_selection, X, y,
            variable_names=problem.variable_names,
        )
        self._last_v60_final_model_audit = final_audit
        return build_native_v60_result(final_audit) if final_audit.get("execution_status") == "selected" else {
            "success": False, "error": "NO_CREDIBLE_CANDIDATE",
            "formula": "N/A", "expression": "N/A", "final_formula": "N/A",
            "strategy": "native_v60",
        }

    def evaluate_native_far_set(self, X_far: Any, y_far: Any) -> dict[str, Any]:
        """Evaluate only the frozen finalized model; this method cannot change selection."""
        if self._last_v60_activate_native_result is not True:
            raise RuntimeError("native V60 activation must complete before far evaluation")
        if self._last_v60_final_model_audit.get("execution_status") != "selected":
            raise RuntimeError("a selected frozen native V60 final model is required")
        audit = evaluate_frozen_native_v60_model(
            self._last_v60_final_model_audit, X_far, y_far,
            variable_names=self._last_v60_run_context.variable_names,
        )
        self._last_v60_far_evaluation_audit = audit
        return dict(audit)

    def discover(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Run native V60 discovery; preserve V50.2 unless explicit handoff is requested."""
        self._reset_v60_call_state()
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

        prepared, run_context = _prepare_v60_contract_context(
            X, y, var_names, metadata, self.domain
        )
        activation_requested = prepared.get("v60_activate_native_model", False)
        if not isinstance(activation_requested, bool):
            raise TypeError("v60_activate_native_model must be a boolean")
        if activation_requested:
            far_metadata_keys = {
                "X_far", "y_far", "far_X", "far_y",
                "v60_far_X", "v60_far_y", "far_evaluation_data",
            }
            if far_metadata_keys.intersection(prepared):
                raise ValueError(
                    "far/evaluation data must be supplied only to evaluate_native_far_set() after finalization"
                )
            if run_context is None:
                raise ValueError(
                    "v60_activate_native_model=true requires a typed DiscoveryProblem contract"
                )
            far_keys = {
                "X_far", "y_far", "far_X", "far_y",
                "v60_far_X", "v60_far_y", "far_evaluation_data",
            }
            problem_metadata = prepared["discovery_problem"].metadata
            if far_keys.intersection(kwargs) or far_keys.intersection(prepared) or far_keys.intersection(problem_metadata):
                raise ValueError(
                    "far/evaluation arrays are not accepted by discover() or the problem metadata; "
                    "use evaluate_native_far_set() after finalization"
                )
            external_spec = prepared.get("v60_external_candidate_proposals", {})
            if external_spec is None:
                external_spec = {}
            if not isinstance(external_spec, Mapping):
                raise TypeError("v60_external_candidate_proposals must be a mapping")
            self._last_v60_run_context = run_context
            self._last_v60_activate_native_result = True
            native_result = self._run_native_v60_training_pipeline(
                X, y, prepared["discovery_problem"], external_spec,
            )
            return self._annotate_v60_result(native_result)
        self._last_v60_run_context = run_context
        self._last_v60_candidate_proposals = ()
        self._last_v60_normalization_audit = {}
        self._last_v60_fitting_audit = {}
        if self._last_v60_run_context is not None:
            problem = prepared["discovery_problem"]
            generated = list(generate_native_template_candidates(problem))
            external_spec = prepared.get("v60_external_candidate_proposals", {}) or {}
            if not isinstance(external_spec, Mapping):
                raise TypeError("v60_external_candidate_proposals must be a mapping")
            unknown_producer_fields = set(external_spec) - {
                "llm_proposals", "pysr_proposals", "llm_call_count",
                "llm_token_count", "pysr_search_attempt_count",
            }
            if unknown_producer_fields:
                raise ValueError(f"unknown external producer fields: {sorted(unknown_producer_fields)}")
            external_audit = ingest_external_candidate_proposals(
                problem,
                llm_proposals=external_spec.get("llm_proposals", ()),
                pysr_proposals=external_spec.get("pysr_proposals", ()),
                llm_call_count=external_spec.get("llm_call_count", 0),
                llm_token_count=external_spec.get("llm_token_count", 0),
                pysr_search_attempt_count=external_spec.get("pysr_search_attempt_count", 0),
            )
            combined = external_audit["proposals"] + [item.to_dict() for item in generated]
            combined = combined[:min(problem.budget.max_candidates, problem.budget.max_search_attempts)]
            self._last_v60_external_producer_audit = dict(external_audit)
            normalized = normalize_candidate_proposals(
                combined, variable_names=problem.variable_names,
                max_candidates=problem.budget.max_candidates,
            )
            self._last_v60_candidate_proposals = tuple(item.to_dict() for item in normalized.candidates)
            self._last_v60_normalization_audit = normalized.to_dict()
            self._last_v60_normalization_audit.pop("candidates", None)
            fitted = fit_native_candidates(
                self._last_v60_candidate_proposals, X, y,
                variable_names=problem.variable_names,
                max_candidates=problem.budget.max_candidates,
                max_search_attempts=problem.budget.max_search_attempts,
                max_wall_time_seconds=problem.budget.max_wall_time_seconds,
            )
            self._last_v60_fitting_audit = fitted.to_dict()
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
        """Run the legacy compatibility entry point without leaking V60 call state.

        This historical signature has no typed DiscoveryProblem/metadata
        channel, so it cannot activate the native V60 pipeline. Reset every
        per-call V60 field before delegating; otherwise a prior discover()
        call could cause stale native audits or even a stale native formula
        to be attached to this unrelated legacy result.
        """
        self._reset_v60_call_state()
        result = super().discover_validate_interpret(*args, **kwargs)
        return self._annotate_v60_result(result)
