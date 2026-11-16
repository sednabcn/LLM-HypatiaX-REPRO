"""Offline tests for uncertainty comparison protocol safeguards."""
import numpy as np
import pytest

from hypatiax.tools.uncertainty_methods.protocol import (
    ComparisonProtocol,
    validate_split_indices,
)


def test_default_protocol_is_valid():
    protocol = ComparisonProtocol()
    assert protocol.validate() is protocol
    assert protocol.nominal_coverages == (0.80, 0.90, 0.95)


def test_protocol_rejects_missing_train_or_test():
    with pytest.raises(ValueError, match="train and test"):
        ComparisonProtocol(split_roles=("train", "calibration")).validate()


def test_protocol_rejects_invalid_coverage_and_duplicate_seed():
    with pytest.raises(ValueError, match="strictly between"):
        ComparisonProtocol(nominal_coverages=(0.8, 1.0)).validate()
    with pytest.raises(ValueError, match="unique"):
        ComparisonProtocol(seeds=(1, 1)).validate()


def test_split_indices_are_normalized_and_disjoint():
    result = validate_split_indices(
        {"train": [0, 1, 2], "calibration": [3], "test": np.array([4, 5])},
        n_samples=6,
        required_roles=("train", "calibration", "test"),
    )
    assert result["train"].dtype.kind in "iu"
    assert result["test"].tolist() == [4, 5]


@pytest.mark.parametrize(
    "splits, message",
    [
        ({"train": [0, 1], "test": [1, 2]}, "Data leakage"),
        ({"train": [0, 0], "test": [1]}, "duplicate"),
        ({"train": [-1], "test": [1]}, "outside"),
        ({"train": [0.5], "test": [1]}, "integers"),
        ({"train": [], "test": [1]}, "non-empty"),
        ({"train": [[0, 1]], "test": [2]}, "1D"),
    ],
)
def test_split_indices_reject_invalid_splits(splits, message):
    with pytest.raises(ValueError, match=message):
        validate_split_indices(splits, n_samples=3)


def test_split_indices_reject_missing_required_role():
    with pytest.raises(ValueError, match="Missing required"):
        validate_split_indices({"train": [0]}, n_samples=2)
