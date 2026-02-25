from contextlib import nullcontext

import numpy as np
import pytest

import packflow.exceptions as exceptions
from packflow.backend import validation


@pytest.mark.parametrize(
    "inputs, expectation",
    [
        ([{"test": 5}], nullcontext()),
        ({"test": 5}, pytest.raises(exceptions.InferenceBackendValidationError)),
        ([1, 2, 3], pytest.raises(exceptions.InferenceBackendValidationError)),
        (5, pytest.raises(exceptions.InferenceBackendValidationError)),
    ],
)
def test__input_is_correct_format(inputs, expectation):
    with expectation:
        validation._input_is_correct_format(inputs)


@pytest.mark.parametrize(
    "inputs, outputs, expectation",
    [
        ([{}], [{}], nullcontext()),
        ([{}], [], pytest.raises(exceptions.InferenceBackendValidationError)),
        ([{}], [{}, {}], pytest.raises(exceptions.InferenceBackendValidationError)),
    ],
)
def test__inputs_and_outputs_match_len(inputs, outputs, expectation):
    with expectation:
        validation._inputs_and_outputs_match_len(inputs, outputs)


@pytest.mark.parametrize(
    "outputs, expectation",
    [
        ([{"test": 5}], nullcontext()),
        ([1, 2, 3], pytest.raises(exceptions.InferenceBackendValidationError)),
        (5, pytest.raises(exceptions.InferenceBackendValidationError)),
    ],
)
def test__output_is_list_of_dicts(outputs, expectation):
    with expectation:
        validation._output_is_list_of_dicts(outputs)


@pytest.mark.parametrize(
    "outputs, expectation",
    [
        ([{"test": 5}], nullcontext()),
        (
            [{"test": np.int32(5)}],
            pytest.raises(exceptions.InferenceBackendValidationError),
        ),
        (
            [{"test": np.array([1, 2, 3])}],
            pytest.raises(exceptions.InferenceBackendValidationError),
        ),
    ],
)
def test__output_is_json_serializable(outputs, expectation):
    with expectation:
        validation._output_is_json_serializable(outputs)
