"""Reusable evaluation helpers for experiment partitions."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np


def add_noise_matched_extrapolation(
    extrapolation: Mapping[str, tuple[Any, Any]],
    seed: int,
    noise_level: float,
    reference_y: Any,
) -> dict[str, tuple[Any, np.ndarray]]:
    """Return noisy targets using noise_level * std(full clean reference_y).

    Each regime uses RandomState(seed + 1999 + regime_index). Clean inputs
    and target arrays are not modified. Mapping insertion order defines the
    regime index and therefore the deterministic random stream.
    """
    if not isinstance(extrapolation, Mapping):
        raise TypeError("extrapolation must map regime names to (X, y) pairs")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    try:
        level = float(noise_level)
    except (TypeError, ValueError) as exc:
        raise TypeError("noise_level must be a finite non-negative number") from exc
    if not np.isfinite(level) or level < 0:
        raise ValueError("noise_level must be a finite non-negative number")

    reference = np.asarray(reference_y, dtype=float).reshape(-1)
    if reference.size == 0 or not np.isfinite(reference).all():
        raise ValueError("reference_y must contain finite, non-empty clean targets")
    scale = float(level * np.std(reference))

    result: dict[str, tuple[Any, np.ndarray]] = {}
    for index, (regime, pair) in enumerate(extrapolation.items()):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f"regime {regime!r} must contain an (X, y) pair")
        X_part, y_clean = pair
        clean = np.asarray(y_clean, dtype=float).reshape(-1)
        if clean.size == 0 or not np.isfinite(clean).all():
            raise ValueError(f"regime {regime!r} targets must be finite and non-empty")
        rng = np.random.RandomState(int(seed) + 1999 + index)
        noisy = clean + rng.normal(0.0, scale, size=len(clean))
        result[str(regime)] = (X_part, noisy)
    return result


__all__ = ["add_noise_matched_extrapolation"]
