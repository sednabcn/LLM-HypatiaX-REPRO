"""Leakage-safe fold-local Hybrid/PySR search used by Exp2.

The adapter mirrors HybridDiscoverySystem's outer signed-log transform and
SymbolicEngine's fold-fitted X scaling plus GM/ratio feature engineering.
Each fold gets a fresh pure-PySR engine; LLM guidance is reserved for the
single final full-training discovery after a search configuration is chosen.
"""
from __future__ import annotations

import copy
import os
from typing import Any

import numpy as np

from .symbolic_engine import DiscoveryConfig, SymbolicEngine
from .training_validation import (
    FoldFeaturePreprocessor,
    evaluate_candidate_on_training_folds,
    make_symbolic_refit_predictor,
    make_training_folds,
)
from .pysr_training_search import evaluate_pysr_search_on_training_folds
from .structural_matching import match_fold_discovered_structures
from .pysr_strategy_selection import (
    TrainingOnlySearchSelection,
    select_pysr_search_strategy_on_training_folds,
)


def _signed_log10(values: np.ndarray) -> np.ndarray:
    return np.sign(values) * np.log10(np.abs(values) + 1.0)


def _outer_log_flags(X: np.ndarray, y: np.ndarray) -> tuple[list[bool], bool]:
    """Fit HybridDiscoverySystem's outer log flags on this fold's fit rows."""
    flags: list[bool] = []
    for column in range(X.shape[1]):
        values = np.abs(X[:, column])
        nonzero = values[np.isfinite(values) & (values != 0)]
        if nonzero.size < 2:
            flags.append(False)
            continue
        range_trigger = (
            np.log10(float(nonzero.max())) - np.log10(float(nonzero.min())) > 4
        )
        magnitude_trigger = float(np.median(nonzero)) > 1e5
        flags.append(bool(range_trigger or magnitude_trigger))
    y_abs = np.abs(y[np.isfinite(y) & (y != 0)])
    y_log = bool(
        y_abs.size >= 2
        and np.log10(float(y_abs.max())) - np.log10(float(y_abs.min())) > 4
    )
    return flags, y_log


class HybridFoldPySRSearcher:
    """Fresh, fold-fitted PySR adapter with a frozen prediction transform."""

    def __init__(
        self,
        *,
        config: DiscoveryConfig,
        domain: str,
        variable_names: list[str],
        equation_name: str,
        seed: int,
        parsimony: float,
        fold_iterations: int,
        fold_timeout_seconds: int,
        allow_pow: bool | None = None,
    ):
        self.config = copy.deepcopy(config)
        self.domain = str(domain)
        self.variable_names = list(variable_names)
        self.equation_name = str(equation_name)
        self.seed = int(seed)
        self.parsimony = float(parsimony)
        self.fold_iterations = max(5, int(fold_iterations))
        self.fold_timeout_seconds = max(1, int(fold_timeout_seconds))
        self.allow_pow = allow_pow
        self.engine: SymbolicEngine | None = None
        self.expression: str | None = None
        self.x_log_flags: list[bool] = []
        self.y_log = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_fit = np.asarray(X, dtype=float)
        y_fit = np.asarray(y, dtype=float).reshape(-1)
        if X_fit.ndim != 2 or X_fit.shape[1] != len(self.variable_names):
            raise ValueError("fold feature schema does not match variable_names")
        if X_fit.shape[0] != y_fit.size or X_fit.shape[0] < 4:
            raise ValueError("fold fitting arrays are misaligned or too small")
        if not np.isfinite(X_fit).all() or not np.isfinite(y_fit).all():
            raise ValueError("fold fitting arrays must be finite")

        self.x_log_flags, self.y_log = _outer_log_flags(X_fit, y_fit)
        X_engine = X_fit.copy()
        for index, enabled in enumerate(self.x_log_flags):
            if enabled:
                X_engine[:, index] = _signed_log10(X_engine[:, index])
        y_engine = _signed_log10(y_fit) if self.y_log else y_fit.copy()

        cfg = copy.deepcopy(self.config)
        cfg.niterations = min(int(cfg.niterations), self.fold_iterations)
        cfg.populations = min(int(cfg.populations), 5)
        cfg.pysr_timeout = self.fold_timeout_seconds
        cfg.parsimony = self.parsimony
        allow_pow = self.allow_pow
        if allow_pow is None:
            allow_pow = bool(np.isfinite(X_engine).all() and np.min(X_engine) >= 0.0)
        binary = list(cfg.binary_operators or [])
        if allow_pow and "pow" not in binary:
            binary.append("pow")
        elif not allow_pow and "pow" in binary:
            binary.remove("pow")
        cfg.binary_operators = binary

        self.engine = SymbolicEngine(config=cfg, domain=self.domain)
        env_keys = ("PYSR_TIMEOUT", "N_ITERATIONS", "POPULATIONS")
        old_env = {key: os.environ.get(key) for key in env_keys}
        os.environ["PYSR_TIMEOUT"] = str(self.fold_timeout_seconds)
        os.environ["N_ITERATIONS"] = str(cfg.niterations)
        os.environ["POPULATIONS"] = str(cfg.populations)
        try:
            result = self.engine.discover(
                X_engine,
                y_engine,
                variable_names=self.variable_names,
                equation_name=self.equation_name,
                random_state=self.seed,
            )
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        expression = str((result or {}).get("expression") or "").strip()
        if (
            not expression
            or expression in {"DISCOVERY_FAILED", "NO_VALID_EQUATIONS", "VALIDATION_FAILED"}
            or getattr(self.engine, "_last_fold_transform_state", None) is None
        ):
            raise RuntimeError("fold-local SymbolicEngine search produced no usable model")
        self.expression = expression
        return self

    def get_best(self) -> dict[str, str]:
        if not self.expression:
            raise ValueError("fold search has not produced an equation")
        return {"equation": self.expression}

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.engine is None:
            raise ValueError("fold searcher is not fitted")
        X_validation = np.asarray(X, dtype=float).copy()
        if X_validation.ndim != 2 or X_validation.shape[1] != len(self.x_log_flags):
            raise ValueError("validation feature schema differs from fold fit schema")
        for index, enabled in enumerate(self.x_log_flags):
            if enabled:
                X_validation[:, index] = _signed_log10(X_validation[:, index])
        prediction = np.asarray(
            self.engine.predict_fold_validation(X_validation), dtype=float
        ).reshape(-1)
        if self.y_log:
            exponent = np.clip(np.abs(prediction), 0.0, 308.0)
            prediction = np.sign(prediction) * (np.power(10.0, exponent) - 1.0)
        if prediction.shape != (X_validation.shape[0],) or not np.isfinite(prediction).all():
            raise FloatingPointError("fold-local Hybrid/PySR prediction is invalid")
        return prediction


def select_hybrid_search_configuration(
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    variable_names: list[str],
    equation_name: str,
    domain: str,
    base_config: DiscoveryConfig,
    seed: int = 42,
    n_splits: int = 2,
    validation_fraction: float = 0.2,
    fold_iterations: int = 20,
    fold_timeout_seconds: int = 20,
    allow_pow: bool | None = None,
    max_mean_normalized_rmse: float | None = None,
) -> tuple[TrainingOnlySearchSelection, dict[str, float]]:
    """Choose a PySR parsimony configuration using only internal training folds."""
    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float).reshape(-1)
    folds = make_training_folds(
        X.shape[0],
        n_splits=int(n_splits),
        n_repeats=1,
        validation_fraction=float(validation_fraction),
        seed=int(seed),
        strategy="repeated_random",
    )

    base = float(base_config.parsimony)
    parsimony_by_strategy = {
        "baseline": base,
        "lower_parsimony": max(base * 0.5, 1e-6),
        "higher_parsimony": min(base * 2.0, 1.0),
    }
    factories: dict[str, Any] = {}
    for strategy_name, parsimony in parsimony_by_strategy.items():
        factories[strategy_name] = (
            lambda fold_seed, p=parsimony: HybridFoldPySRSearcher(
                config=base_config,
                domain=domain,
                variable_names=variable_names,
                equation_name=equation_name,
                seed=fold_seed,
                parsimony=p,
                fold_iterations=fold_iterations,
                fold_timeout_seconds=fold_timeout_seconds,
                allow_pow=allow_pow,
            )
        )

    selection = select_pysr_search_strategy_on_training_folds(
        factories,
        X,
        y,
        folds,
        seed=int(seed),
        minimum_valid_folds=len(folds),
        max_mean_normalized_rmse=max_mean_normalized_rmse,
    )
    return selection, parsimony_by_strategy


def evaluate_hybrid_candidate_on_training_folds(
    expression: str,
    candidate_variable_names: list[str],
    raw_feature_names: list[str],
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds,
    *,
    minimum_valid_folds: int = 2,
    max_nfev: int = 500,
):
    """Evaluate an engine-space candidate with all transforms learned per fold.

    Supports candidate schemas containing raw, geometric-mean, and directed
    ratio symbols. Feature pairs are reconstructed from the candidate schema;
    signed-log/scaling and target transforms are learned from each fit partition.
    """
    from .training_validation import evaluate_engine_candidate_on_training_folds

    return evaluate_engine_candidate_on_training_folds(
        expression,
        candidate_variable_names,
        raw_feature_names,
        X_train,
        y_train,
        tuple(folds),
        minimum_valid_folds=minimum_valid_folds,
        max_nfev=max_nfev,
    )



__all__ = [
    "HybridFoldPySRSearcher",
    "select_hybrid_search_configuration",
    "evaluate_hybrid_candidate_on_training_folds",
    "evaluate_nested_hybrid_structure_search_on_training_folds",
]



def evaluate_nested_hybrid_structure_search_on_training_folds(
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds,
    *,
    variable_names: list[str],
    equation_name: str,
    domain: str,
    base_config: DiscoveryConfig,
    parsimony: float | None = None,
    seed: int = 42,
    fold_iterations: int = 20,
    fold_timeout_seconds: int = 20,
    allow_pow: bool | None = None,
    minimum_valid_folds: int = 2,
    minimum_structure_recurrence: int = 2,
    minimum_structure_recurrence_fraction: float = 0.5,
) -> dict:
    """Run a fresh Hybrid/PySR structural search inside every training fold.

    Unlike fixed-expression coefficient refitting, each fold independently
    discovers its own symbolic structure using only that fold's fitting rows.
    The held-out partition is passed only to the fitted fold searcher's
    predict() method. This produces procedure-level nested validation evidence;
    it is not a candidate-specific score for an equation discovered later on
    the complete training region.
    """
    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float).reshape(-1)
    fold_tuple = tuple(folds)
    if X.ndim != 2 or X.shape[0] != y.size:
        raise ValueError("X_train must be 2D and aligned with y_train")
    if X.shape[1] != len(variable_names):
        raise ValueError("variable_names do not match X_train columns")
    if not fold_tuple:
        raise ValueError("at least one training fold is required")
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("training arrays must contain only finite values")
    if minimum_valid_folds < 1 or minimum_valid_folds > len(fold_tuple):
        raise ValueError("minimum_valid_folds must be within the supplied fold count")

    selected_parsimony = (
        float(base_config.parsimony) if parsimony is None else float(parsimony)
    )

    def make_searcher(fold_seed: int):
        return HybridFoldPySRSearcher(
            config=base_config,
            domain=domain,
            variable_names=list(variable_names),
            equation_name=equation_name,
            seed=fold_seed,
            parsimony=selected_parsimony,
            fold_iterations=fold_iterations,
            fold_timeout_seconds=fold_timeout_seconds,
            allow_pow=allow_pow,
        )

    summary = evaluate_pysr_search_on_training_folds(
        make_searcher,
        X,
        y,
        fold_tuple,
        seed=int(seed),
        minimum_valid_folds=minimum_valid_folds,
    )
    result = summary.to_dict()
    structure_matching = match_fold_discovered_structures(
        result.get("fold_searches", []),
        (result.get("validation") or {}).get("fold_metrics", []),
        variable_names,
        minimum_recurrence=minimum_structure_recurrence,
        minimum_recurrence_fraction=minimum_structure_recurrence_fraction,
        total_fold_count=len(fold_tuple),
    )
    result.update({
        "structure_matching": structure_matching,
        "candidate_structures": structure_matching["structures"],
        "validation_design": "nested_fresh_symbolic_search_per_training_fold",
        "selection_role": "discovery_procedure_validation_only",
        "candidate_specific_score": False,
        "fold_structures_are_not_averaged": True,
        "structure_stability_is_diagnostic_only": True,
        "far_test_data_used": False,
        "llm_enabled_in_fold_search": False,
        "final_full_training_discovery_required": True,
    })
    return result


