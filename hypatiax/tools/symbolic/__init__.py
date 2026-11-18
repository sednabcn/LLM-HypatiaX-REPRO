"""Public, lazy exports for HypatiaX symbolic-regression tools."""

from importlib import import_module

__all__ = [
    "PhysicsAwareRegressor",
    "HybridDiscoverySystemV60",
    "create_hybrid_discovery_system",
    "create_hybrid_discovery_system_from_config",
    "SymbolicEngine",
    "SymbolicEngineWithLLM",
    "DiscoveryConfig",
    "LLMConfig",
    "DiscoveryProblem",
    "discovery_problem_from_dict",
    "DiscoveryBudget",
    "ConstraintSpec",
    "ConstraintOutcome",
    "CandidateRecord",
    "DiscoveryReport",
    "CandidateValidator",
    "FoldFeaturePreprocessor",
    "FoldFeaturePlan",
    "FoldFeaturePipeline",
    "FoldTargetScaler",
    "FoldCandidateFeaturePipeline",
    "FoldTargetPreprocessor",
    "evaluate_engine_candidate_on_training_folds",
    "make_fold_preprocessed_symbolic_predictor",
    "evaluate_preprocessed_symbolic_candidate_on_training_folds",
    "TrainingFold",
    "FoldMetric",
    "CandidateValidationSummary",
    "make_training_folds",
    "evaluate_candidate_on_training_folds",
    "make_symbolic_refit_predictor",
    "evaluate_symbolic_candidate_on_training_folds",
    "expression_stability",
    "PySRFoldSearchSummary",
    "evaluate_pysr_search_on_training_folds",
    "SearchStrategyScore",
    "TrainingOnlySearchSelection",
    "select_pysr_search_strategy_on_training_folds",
    "HybridFoldPySRSearcher",
    "select_hybrid_search_configuration",
    "evaluate_hybrid_candidate_on_training_folds",
    "evaluate_nested_hybrid_structure_search_on_training_folds",
    "canonicalize_symbolic_structure",
    "match_fold_discovered_structures",
    "crosswalk_full_training_candidate_to_fold_structure",
    "select_pareto_discovery_report",
    "evaluate_selected_native_candidate_on_far_set",
    "seal_discovery_report",
    "verify_discovery_report_envelope",
    "ingest_external_candidate_proposals",
]


def __getattr__(name: str):
    """Load symbolic implementations only when their public names are requested."""
    if name in {"HybridDiscoverySystemV60", "create_hybrid_discovery_system", "create_hybrid_discovery_system_from_config"}:
        module = import_module(".hybrid_system_factory", __name__) if name != "HybridDiscoverySystemV60" else import_module(".hybrid_system_v60", __name__)
    elif name == "PhysicsAwareRegressor":
        module = import_module(".physics_aware_regressor", __name__)
    elif name in {
        "SymbolicEngine",
        "SymbolicEngineWithLLM",
        "DiscoveryConfig",
        "LLMConfig",
    }:
        module = import_module(".symbolic_engine", __name__)
    elif name == "CandidateValidator":
        module = import_module(".discovery_validation", __name__)
    elif name in {
        "FoldFeaturePreprocessor", "FoldFeaturePlan", "FoldFeaturePipeline",
        "FoldTargetScaler", "FoldCandidateFeaturePipeline", "FoldTargetPreprocessor",
        "evaluate_engine_candidate_on_training_folds", "make_fold_preprocessed_symbolic_predictor",
        "evaluate_preprocessed_symbolic_candidate_on_training_folds",
        "TrainingFold", "FoldMetric", "CandidateValidationSummary",
        "make_training_folds", "evaluate_candidate_on_training_folds",
        "make_symbolic_refit_predictor", "evaluate_symbolic_candidate_on_training_folds",
        "expression_stability",
    }:
        module = import_module(".training_validation", __name__)
    elif name in {
        "PySRFoldSearchSummary", "evaluate_pysr_search_on_training_folds",
    }:
        module = import_module(".pysr_training_search", __name__)
    elif name in {
        "SearchStrategyScore", "TrainingOnlySearchSelection",
        "select_pysr_search_strategy_on_training_folds",
    }:
        module = import_module(".pysr_strategy_selection", __name__)
    elif name in {
        "HybridFoldPySRSearcher", "select_hybrid_search_configuration",
        "evaluate_hybrid_candidate_on_training_folds",
        "evaluate_nested_hybrid_structure_search_on_training_folds",
    }:
        module = import_module(".hybrid_fold_search", __name__)
    elif name in {
        "canonicalize_symbolic_structure",
        "match_fold_discovered_structures",
        "crosswalk_full_training_candidate_to_fold_structure",
    }:
        module = import_module(".structural_matching", __name__)
    elif name == "select_pareto_discovery_report":
        module = import_module(".pareto_discovery", __name__)
    elif name == "evaluate_selected_native_candidate_on_far_set":
        module = import_module(".v60_frozen_far_evaluation", __name__)
    elif name in {"seal_discovery_report", "verify_discovery_report_envelope"}:
        module = import_module(".discovery_report_integrity", __name__)
    elif name == "ingest_external_candidate_proposals":
        module = import_module(".v60_external_producers", __name__)
    elif name in {
        "DiscoveryProblem",
        "discovery_problem_from_dict",
        "DiscoveryBudget",
        "ConstraintSpec",
        "ConstraintOutcome",
        "CandidateRecord",
        "DiscoveryReport",
    }:
        module = import_module(".discovery_contracts", __name__)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
