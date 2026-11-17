"""Public, lazy exports for HypatiaX symbolic-regression tools."""

from importlib import import_module

__all__ = [
    "PhysicsAwareRegressor",
    "SymbolicEngine",
    "SymbolicEngineWithLLM",
    "DiscoveryConfig",
    "LLMConfig",
    "DiscoveryProblem",
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
]


def __getattr__(name: str):
    """Load symbolic implementations only when their public names are requested."""
    if name == "PhysicsAwareRegressor":
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
        "FoldFeaturePreprocessor", "FoldFeaturePlan", "FoldFeaturePipeline", "FoldTargetScaler", "make_fold_preprocessed_symbolic_predictor", "evaluate_preprocessed_symbolic_candidate_on_training_folds", "TrainingFold", "FoldMetric", "CandidateValidationSummary",
        "make_training_folds", "evaluate_candidate_on_training_folds",
        "make_symbolic_refit_predictor", "evaluate_symbolic_candidate_on_training_folds",
        "expression_stability",
    }:
        module = import_module(".training_validation", __name__)
    elif name in {
        "DiscoveryProblem",
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
