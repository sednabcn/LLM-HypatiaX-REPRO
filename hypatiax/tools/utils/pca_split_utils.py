"""
Reusable PCA-directed train/test split utility for HypatiaX benchmarks.

The split orders samples along the first principal component. The lower
PC1 region is used for training and the upper region for testing.
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


def pca_directed_split(X, y, test_size=0.6, random_state=None):
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
    component = pca.components_[0]
    anchor = int(np.argmax(np.abs(component)))
    if component[anchor] < 0:
        pc1_scores = -pc1_scores

    # Stable sort; original row position breaks equal-score ties.
    original_positions = np.arange(n_samples)
    order = np.lexsort((original_positions, pc1_scores))

    split_point = int(n_samples * (1.0 - test_size))
    split_point = max(1, min(split_point, n_samples - 1))

    train_idx = order[:split_point]
    test_idx = order[split_point:]

    return (
        X_array[train_idx],
        X_array[test_idx],
        y_array[train_idx],
        y_array[test_idx],
    )
