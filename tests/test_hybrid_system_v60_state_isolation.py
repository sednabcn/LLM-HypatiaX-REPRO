"""Regression tests for V60 per-call audit isolation."""

from hypatiax.tools.symbolic.hybrid_system_v60 import HybridDiscoverySystemV60


def test_v60_call_reset_clears_all_previous_native_audits():
    engine = object.__new__(HybridDiscoverySystemV60)
    fields = (
        "_last_v60_run_context",
        "_last_v60_candidate_proposals",
        "_last_v60_normalization_audit",
        "_last_v60_fitting_audit",
        "_last_v60_training_fit_audit",
        "_last_v60_multi_basis_fit_audit",
        "_last_v60_multi_basis_validation_audit",
        "_last_v60_multi_basis_evidence_audit",
        "_last_v60_multi_basis_selection_audit",
        "_last_v60_gate_audit",
        "_last_v60_training_validation_audit",
        "_last_v60_objective_selection_audit",
        "_last_v60_residual_stability_audit",
        "_last_v60_external_producer_audit",
        "_last_v60_final_model_audit",
        "_last_v60_far_evaluation_audit",
    )
    for field in fields:
        setattr(engine, field, {"stale": True})
    engine._last_v60_activate_native_result = True

    engine._reset_v60_call_state()

    for field in fields:
        value = getattr(engine, field)
        assert value == (() if field == "_last_v60_candidate_proposals" else None if field == "_last_v60_run_context" else {})
    assert engine._last_v60_activate_native_result is False


def test_v60_call_reset_is_idempotent():
    engine = object.__new__(HybridDiscoverySystemV60)
    engine._reset_v60_call_state()
    first = engine._last_v60_final_model_audit
    engine._reset_v60_call_state()
    assert engine._last_v60_final_model_audit == first == {}
