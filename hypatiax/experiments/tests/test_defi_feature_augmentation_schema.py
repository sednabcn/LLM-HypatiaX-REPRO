"""Regression tests for train-fitted DeFi NN feature augmentation."""

import importlib

import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler


@pytest.mark.parametrize(
    "module_name",
    [
        "hypatiax.experiments.benchmarks.hypatiax_defi_benchmark_v3c",
        "hypatiax.experiments.benchmarks.hypatiax_defi_benchmark_pca",
    ],
)
def test_feature_augmentation_uses_one_training_fitted_schema(module_name):
    benchmark = importlib.import_module(module_name)

    # Training column 0 is positive; column 1 contains a negative value.
    # The held-out split reverses those domain patterns. Inferring optional
    # transforms independently would therefore produce different widths.
    X_train = np.array([[1.0, -2.0], [2.0, 3.0], [4.0, 5.0]])
    X_test = np.array([[-1.0, 2.0], [3.0, 4.0]])

    schema = benchmark._feature_augmentation_schema(X_train)
    train_aug = benchmark._augment_features(X_train, schema=schema)
    test_aug = benchmark._augment_features(X_test, schema=schema)

    assert train_aug.shape[1] == test_aug.shape[1]
    assert np.isfinite(train_aug).all()
    assert np.isfinite(test_aug).all()

    # The fitted scaler must accept the held-out matrix without a width error.
    scaler = StandardScaler().fit(train_aug)
    transformed_test = scaler.transform(test_aug)
    assert transformed_test.shape == test_aug.shape
