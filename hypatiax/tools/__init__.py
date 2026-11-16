"""HypatiaX tools: symbolic regression, extrapolation, and uncertainty utilities."""

from .feynman_horizon import evaluate_feynman_horizon_curves
from .extrapolation_horizon import (
    evaluate_horizon_scenarios,
    generate_horizon_scenarios,
    plot_horizon_curves,
    score_predictions,
    write_results_json,
)
from .uncertainty import (
    SplitConformalRegressor,
    evaluate_interval_levels,
    evaluate_prediction_intervals,
)

__all__ = [
    "generate_horizon_scenarios",
    "score_predictions",
    "evaluate_horizon_scenarios",
    "write_results_json",
    "plot_horizon_curves",
    "evaluate_feynman_horizon_curves",
    "SplitConformalRegressor",
    "evaluate_prediction_intervals",
    "evaluate_interval_levels",
]
