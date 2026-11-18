"""Training-only comparison of alternative fresh-PySR search strategies.

This selects a search configuration, not a final equation. The selected
configuration must be rerun once on the complete training region to produce
the final equation; far/test data remains reserved for final evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

import numpy as np

from .pysr_training_search import (
    PySRFoldSearchSummary,
    evaluate_pysr_search_on_training_folds,
)
from .training_validation import TrainingFold


@dataclass(frozen=True)
class SearchStrategyScore:
    strategy_name: str
    summary: PySRFoldSearchSummary
    mean_normalized_rmse: float
    worst_normalized_rmse: float
    normalized_rmse_std: float
    expression_stability_fraction: float | None
    median_expression_length: float

    def to_dict(self) -> dict:
        return {
            "strategy_name": self.strategy_name,
            "mean_normalized_rmse": self.mean_normalized_rmse,
            "worst_normalized_rmse": self.worst_normalized_rmse,
            "normalized_rmse_std": self.normalized_rmse_std,
            "expression_stability_fraction": self.expression_stability_fraction,
            "median_expression_length": self.median_expression_length,
            "validation": self.summary.to_dict(),
        }


@dataclass(frozen=True)
class TrainingOnlySearchSelection:
    status: str
    selected_strategy: str | None
    ranked_strategies: tuple[SearchStrategyScore, ...]
    rejected_strategies: tuple[dict, ...]
    selection_scope: str = "training_region_only"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "selected_strategy": self.selected_strategy,
            "selection_scope": self.selection_scope,
            "selected_artifact": "search_configuration_only",
            "ranked_strategies": [item.to_dict() for item in self.ranked_strategies],
            "rejected_strategies": [dict(item) for item in self.rejected_strategies],
            "far_test_data_used": False,
            "final_full_training_search_required": self.status == "selected",
        }


def select_pysr_search_strategy_on_training_folds(
    searcher_factories: Mapping[str, Callable[[int], Any]],
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds: tuple[TrainingFold, ...],
    *,
    seed: int = 42,
    minimum_valid_folds: int = 2,
    max_mean_normalized_rmse: float | None = None,
    budget_runtime: Any | None = None,
) -> TrainingOnlySearchSelection:
    """Rank alternative PySR configurations using paired internal folds.

    Every strategy receives the same fold partitions and deterministic seed
    schedule. Each fold creates a fresh estimator through that strategy's
    factory. A strategy is ineligible if too few folds pass or any valid fold
    lacks a finite normalized RMSE. Lower mean normalized RMSE wins; worst
    fold and dispersion are deterministic secondary criteria. Expression
    length is only a final descriptive tie-break, not symbolic complexity.
    """
    if not searcher_factories:
        raise ValueError("at least one named PySR search strategy is required")
    if len(searcher_factories) != len(set(searcher_factories)):
        raise ValueError("strategy names must be unique")
    if minimum_valid_folds < 1:
        raise ValueError("minimum_valid_folds must be >= 1")
    if max_mean_normalized_rmse is not None and (
        not np.isfinite(max_mean_normalized_rmse) or max_mean_normalized_rmse < 0
    ):
        raise ValueError("max_mean_normalized_rmse must be finite and >= 0")

    ranked: list[SearchStrategyScore] = []
    rejected: list[dict] = []
    for name in sorted(searcher_factories):
        if budget_runtime is not None and budget_runtime.expired():
            raise TimeoutError("discovery wall-time budget expired before next search strategy")
        factory = searcher_factories[name]
        try:
            summary = evaluate_pysr_search_on_training_folds(
                factory,
                X_train,
                y_train,
                folds,
                seed=seed,
                minimum_valid_folds=minimum_valid_folds,
                budget_runtime=budget_runtime,
            )
            if budget_runtime is not None and budget_runtime.expired():
                raise TimeoutError("search strategy returned after discovery wall-time deadline")
            metrics = summary.validation.fold_metrics
            normalized = np.asarray(
                [item.normalized_rmse for item in metrics], dtype=float
            )
            if (
                len(metrics) < minimum_valid_folds
                or not np.all(np.isfinite(normalized))
            ):
                raise ValueError("fold evidence lacks finite normalized RMSE")
            mean_nrmse = float(np.mean(normalized))
            worst_nrmse = float(np.max(normalized))
            spread = float(np.std(normalized))
            expressions = [
                item["expression"] for item in summary.fold_searches
                if item.get("expression")
            ]
            stability = None
            if expressions:
                from .training_validation import expression_stability
                stability = expression_stability(expressions)["dominant_fraction"]
            if budget_runtime is not None and budget_runtime.expired():
                raise TimeoutError("search strategy diagnostics returned after discovery wall-time deadline")
            lengths = [len(value) for value in expressions]
            median_length = float(np.median(lengths)) if lengths else float("inf")
            if (
                max_mean_normalized_rmse is not None
                and mean_nrmse > max_mean_normalized_rmse
            ):
                raise ValueError(
                    f"mean normalized RMSE {mean_nrmse:.6g} exceeds configured "
                    f"limit {max_mean_normalized_rmse:.6g}"
                )
            ranked.append(SearchStrategyScore(
                strategy_name=name,
                summary=summary,
                mean_normalized_rmse=mean_nrmse,
                worst_normalized_rmse=worst_nrmse,
                normalized_rmse_std=spread,
                expression_stability_fraction=(
                    float(stability) if stability is not None else None
                ),
                median_expression_length=median_length,
            ))
        except TimeoutError:
            raise
        except Exception as exc:
            rejected.append({
                "strategy_name": name,
                "reason": f"{type(exc).__name__}: {exc}"[:400],
                "eligible": False,
            })

    if budget_runtime is not None and budget_runtime.expired():
        raise TimeoutError("search strategy ranking returned after discovery wall-time deadline")
    ranked.sort(key=lambda item: (
        item.mean_normalized_rmse,
        item.worst_normalized_rmse,
        item.normalized_rmse_std,
        item.median_expression_length,
        item.strategy_name,
    ))
    if not ranked:
        return TrainingOnlySearchSelection(
            status="NO_CREDIBLE_CANDIDATE",
            selected_strategy=None,
            ranked_strategies=(),
            rejected_strategies=tuple(rejected),
        )
    return TrainingOnlySearchSelection(
        status="selected",
        selected_strategy=ranked[0].strategy_name,
        ranked_strategies=tuple(ranked),
        rejected_strategies=tuple(rejected),
    )


__all__ = [
    "SearchStrategyScore",
    "TrainingOnlySearchSelection",
    "select_pysr_search_strategy_on_training_folds",
]
