from contextlib import nullcontext
import json

import numpy as np
import pytest

from packflow.utils.normalize.normalize import ensure_native_types, ensure_valid_output


@pytest.mark.parametrize(
    "obj, expected_result, expectation",
    [
        # base/native scalar types
        (5, 5, nullcontext()),
        (5.0, 5.0, nullcontext()),
        ("5", "5", nullcontext()),
        (True, True, nullcontext()),
        (None, None, nullcontext()),
        # non-native scalar types
        (np.int16(5), 5, nullcontext()),
        # dict/mapping container
        ({"value": 5}, {"value": 5}, nullcontext()),
        ({"value": np.array([1, 2, 3])}, {"value": [1, 2, 3]}, nullcontext()),
        # array-like containers
        ([1, 2, 3], [1, 2, 3], nullcontext()),
        (np.array([1, 2, 3]), [1, 2, 3], nullcontext()),
        ({1, 2, 3}, [1, 2, 3], nullcontext()),
        ((1, 2, 3), [1, 2, 3], nullcontext()),
        # Unsupported type
        (json, None, pytest.raises(TypeError)),
    ],
)
def test_ensure_native_types(obj, expected_result, expectation):
    with expectation:
        result = ensure_native_types(obj)
        assert result == expected_result
        assert json.dumps(result)


@pytest.mark.parametrize(
    "func_kwargs, expected_output, expectation",
    [
        (dict(output=[]), [], nullcontext()),
        (
            dict(output=[1, 2, 3]),
            [{"output": 1}, {"output": 2}, {"output": 3}],
            nullcontext(),
        ),
        (
            dict(output=[[1], [2], [3]], parent_key="prediction"),
            [{"prediction": 1}, {"prediction": 2}, {"prediction": 3}],
            nullcontext(),
        ),
        # error
        (dict(output=[json]), None, pytest.raises(TypeError)),
    ],
)
def test_ensure_valid_output(func_kwargs, expected_output, expectation):
    with expectation:
        result = ensure_valid_output(**func_kwargs)
        assert result == expected_output
        assert json.dumps(result)
