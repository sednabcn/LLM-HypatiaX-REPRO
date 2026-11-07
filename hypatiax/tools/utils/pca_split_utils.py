"""
Reusable PCA-directed train/test split utility for HypatiaX benchmarks.

The split orders samples along the first principal component. The lower
PC1 region is used for training and the upper region for testing.
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


def pca_directed_split(X, y, test_size=0.6, random_state=None, feature_names=None, return_metadata=False):
    """
    Create a deterministic PCA-directed train/test split.

    Parameters
    ----------
    X : array-like or pandas.DataFrame
        Numeric feature matrix with shape (n_samples, n_features).
    y : array-like or pandas.Series
        Target vector with one value per sample.
    test_size : float, default=0.6
        Fraction of samples assigned to the test split; must be in (0, 1).
    random_state : int or None, default=None
        Random state passed to PCA.
    feature_names : sequence of str or None, default=None
        Optional feature names used in the audit metadata.
    return_metadata : bool, default=False
        If True, append a JSON-serializable split audit dictionary to the
        four arrays returned by default.

    Returns
    -------
    X_train, X_test, y_train, y_test : numpy.ndarray
        Positional train/test partitions.

    Notes
    -----
    PCA is fitted on all feature rows to construct the split. This is a
    transductive split-design procedure, not an inductive preprocessing
    pipeline. The sign of PC1 is oriented so its largest-absolute loading
    is positive, making the direction consistent for a given feature order.
    """

    if not isinstance(test_size, (int, float, np.integer, np.floating)):
        raise ValueError("test_size must be a number.")

    if not np.isfinite(test_size) or not 0 < test_size < 1:
        raise ValueError(
            f"test_size must be finite and between 0 and 1; got {test_size!r}"
        )

    try:
        X_array = np.asarray(X, dtype=float)
        y_array = np.asarray(y)
    except (TypeError, ValueError) as exc:
        raise ValueError("X and y must contain valid array-like data.") from exc

    if X_array.ndim != 2:
        raise ValueError(
            f"X must be a 2D feature matrix; got {X_array.ndim} dimensions."
        )

    if y_array.ndim == 2 and y_array.shape[1] == 1:
        y_array = y_array.ravel()
    elif y_array.ndim != 1:
        raise ValueError("y must be a one-dimensional target vector.")

    n_samples, n_features = X_array.shape

    if n_samples < 2:
        raise ValueError("Need at least 2 samples for a PCA split.")

    if n_features < 1:
        raise ValueError("Need at least 1 feature.")

    if y_array.shape[0] != n_samples:
        raise ValueError(
            f"X has {n_samples} samples but y has {y_array.shape[0]}."
        )

    if not np.isfinite(X_array).all():
        raise ValueError("X contains NaN or infinite values.")

    if np.issubdtype(y_array.dtype, np.number):
        if not np.isfinite(y_array).all():
            raise ValueError("y contains NaN or infinite values.")

    pca = PCA(n_components=1, random_state=random_state)
    pc1_scores = pca.fit_transform(X_array).ravel()

    # Orient PC1 consistently: its largest-absolute loading is positive.
    component = pca.components_[0].copy()
    anchor = int(np.argmax(np.abs(component)))
    if component[anchor] < 0:
        pc1_scores = -pc1_scores
        component = -component

    # Stable sort; original row position breaks equal-score ties.
    original_positions = np.arange(n_samples)
    order = np.lexsort((original_positions, pc1_scores))

    split_point = int(n_samples * (1.0 - test_size))
    split_point = max(1, min(split_point, n_samples - 1))

    train_idx = order[:split_point]
    test_idx = order[split_point:]

    result = (
        X_array[train_idx],
        X_array[test_idx],
        y_array[train_idx],
        y_array[test_idx],
    )
    if not return_metadata:
        return result

    if feature_names is None:
        names = [f"x{i}" for i in range(n_features)]
    else:
        names = [str(name) for name in feature_names]
        if len(names) != n_features:
            raise ValueError(
                f"feature_names has {len(names)} entries for {n_features} features."
            )

    feature_summary = {}
    for column, name in enumerate(names):
        values = X_array[:, column]
        feature_summary[name] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }

    metadata = {
        "split_protocol": "pca_40_60_pc1",
        "split_method": "PCA(n_components=1) on raw, unstandardized features",
        "feature_scaling": "none",
        "n_samples": int(n_samples),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "test_size": float(test_size),
        "random_state": random_state,
        "split_is_transductive": True,
        "pc1_explained_variance_ratio": float(pca.explained_variance_ratio_[0]),
        "pc1_loadings": {
            name: float(loading)
            for name, loading in zip(names, component)
        },
        "feature_summary": feature_summary,
        "pc1_score_min": float(np.min(pc1_scores)),
        "pc1_score_max": float(np.max(pc1_scores)),
    }
    return result + (metadata,)


def first_feature_percentile_split(X, y, return_metadata=False):
    """Reproduce the historical first-feature 40/60 split without PCA."""
    X_array = np.asarray(X, dtype=float)
    y_array = np.asarray(y)
    if X_array.ndim == 1:
        X_array = X_array.reshape(-1, 1)
    if X_array.ndim != 2:
        raise ValueError(f"X must be a 2D feature matrix; got {X_array.ndim} dimensions.")
    if y_array.ndim == 2 and y_array.shape[1] == 1:
        y_array = y_array.ravel()
    if y_array.ndim != 1 or y_array.shape[0] != len(X_array):
        raise ValueError("y must be a 1D target vector with one value per sample.")
    if len(X_array) == 0 or X_array.shape[1] == 0:
        raise ValueError("X must contain at least one sample and one feature.")

    values = X_array[:, 0]
    threshold = np.percentile(values, 40)
    train_mask = values <= threshold
    test_mask = values > threshold
    if train_mask.sum() < 20 or test_mask.sum() < 20:
        positions = np.arange(len(X_array))
        train_mask = positions < int(0.4 * len(positions))
        test_mask = ~train_mask

    result = (
        X_array[train_mask], y_array[train_mask],
        X_array[test_mask], y_array[test_mask],
    )
    if not return_metadata:
        return result
    metadata = {
        "split_protocol": "first_feature_percentile_40_60",
        "split_method": "40th percentile threshold on first feature",
        "feature_scaling": "none",
        "n_samples": int(len(X_array)),
        "n_train": int(len(result[0])),
        "n_test": int(len(result[2])),
        "split_is_transductive": False,
    }
    return result + (metadata,)


def select_case_by_identity(case_rows, domain, name):
    """Select exactly one protocol case by its stable domain/name identity.

    Returns the (index, case) pair. Missing or duplicate identities fail
    loudly instead of silently choosing a fuzzy substring match.
    """
    matches = [
        (index, case)
        for index, case in enumerate(case_rows)
        if case.get("domain") == domain
        and (case.get("name") or case.get("description")) == name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one case {domain!r}/{name!r}; found {len(matches)}."
        )
    return matches[0]
