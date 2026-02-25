from contextlib import nullcontext

import numpy as np
import pytest
from packflow.utils.data import (
    flatten_dict,
    flatten_records,
    get_nested_field,
    records_to_ndarray,
)


@pytest.mark.parametrize(
    "obj, field, expected",
    [
        ({"foo": {"bar": 5}}, "foo.bar", 5),  # Nested field not directly in obj
        ({"top_level": 42}, "top_level", 42),  # Direct top-level field
        ({}, "missing.field", None),  # Missing field in empty dict
        ({"empty": {}}, "empty.nested", None),  # Nested field with empty dict
    ],
)
def test_get_nested_field(obj, field, expected):
    """Test field retrieval and missing fields."""
    assert get_nested_field(obj, field) == expected


def test_get_nested_field_direct_access():
    """Test direct access to top-level fields."""
    obj = {"direct": 42}
    assert get_nested_field(obj, "direct") == 42


def test_get_nested_field_special_chars():
    """Test handling of special characters in field names."""
    obj = {"special:chars": {"key:123": 999}}
    assert get_nested_field(obj, "special:chars.key:123") == 999
    assert get_nested_field(obj, "special:chars:key:123") is None


def test_get_nested_field_special_chars_custom_delimiter():
    """Test handling of special characters in field names."""
    obj = {"special:chars": {"key:123": 999}}
    assert get_nested_field(obj, "special:chars.key:123", delimiter=":") is None
    assert get_nested_field(obj, "special:chars:key:123", delimiter=":") == 999


# -- Records to NDArray --


@pytest.mark.parametrize(
    "records, feature_names, expectation, expected_result",
    [
        ([], ["num", "num2"], nullcontext(), np.array([])),
        (
            [{"num": 1, "num2": 1}, {"num": 2, "num2": 2}],
            ["num", "num2"],
            nullcontext(),
            np.array([[1, 1], [2, 2]]),
        ),
        (
            [{"num": 1, "num2": 1}, {"num": 2, "num2": 2}],
            ["num", "num3"],
            nullcontext(),
            np.array([[1, None], [2, None]]),
        ),
        ({"num": 1, "num2": 1}, ["num", "num3"], pytest.raises(ValueError), None),
        ([1, 2], ["num"], pytest.raises(ValueError), None),
        ("string", ["num"], pytest.raises(ValueError), None),
    ],
)
def test_records_to_ndarray(records, feature_names, expectation, expected_result):
    with expectation:
        result = records_to_ndarray(records, feature_names)
        assert np.array_equal(result, expected_result)


@pytest.mark.parametrize(
    "dtype",
    ["float32", "int64", "float32", "float64"],
)
def test_records_to_ndarray_dtype(dtype):
    records = [{"num": 1, "num2": 1}, {"num": 2, "num2": 2}]
    feature_names = ["num", "num2"]
    result = records_to_ndarray(records, feature_names, dtype=str(dtype))
    assert result.dtype == dtype


# -- Flattening Utils --


@pytest.mark.parametrize(
    "obj, func_kwargs, expectation, expected_result",
    [
        ({}, {}, nullcontext(), {}),
        (
            {"a": {"b": 1, "c": 2}, "d": [0, 1]},
            dict(delimiter=":"),
            nullcontext(),
            {"a:b": 1, "a:c": 2, "d": [0, 1]},
        ),
        (
            {"a": {"b": 1, "c": 2}, "d": [0, 1]},
            dict(delimiter="."),
            nullcontext(),
            {"a.b": 1, "a.c": 2, "d": [0, 1]},
        ),
        (
            {"a": {"b": 1, "c": 2}, "d": [0, 1]},
            dict(delimiter=":", flatten_lists=True),
            nullcontext(),
            {"a:b": 1, "a:c": 2, "d:0": 0, "d:1": 1},
        ),
        (
            {"a": {"b": 1, "c": 2}, "d": [0, 1]},
            dict(delimiter=".", flatten_lists=True),
            nullcontext(),
            {"a.b": 1, "a.c": 2, "d.0": 0, "d.1": 1},
        ),
        ([0, 1, 2], dict(), pytest.raises(TypeError), {}),
        ("string", dict(), pytest.raises(TypeError), {}),
        (None, dict(), pytest.raises(TypeError), {}),
    ],
)
def test_flatten_dict(obj: dict, func_kwargs: dict, expectation, expected_result):
    with expectation:
        result = flatten_dict(obj, **func_kwargs)
        assert result == expected_result


@pytest.mark.parametrize(
    "records, func_kwargs, expectation, expected_result",
    [
        ([], dict(), nullcontext(), []),
        (
            [{"a": {"b": 1}}, {"c": 2}],
            dict(delimiter=":"),
            nullcontext(),
            [{"a:b": 1}, {"c": 2}],
        ),
        (
            [{"a": {"b": 1}}, {"c": 2}],
            dict(),
            nullcontext(),
            [{"a.b": 1}, {"c": 2}],
        ),
        (
            [{"a": {"b": 1}}, {"c": [0, 1]}],
            dict(delimiter=":", flatten_lists=True),
            nullcontext(),
            [{"a:b": 1}, {"c:0": 0, "c:1": 1}],
        ),
        (
            [{"a": {"b": 1}}, {"c": [0, 1]}],
            dict(flatten_lists=True),
            nullcontext(),
            [{"a.b": 1}, {"c.0": 0, "c.1": 1}],
        ),
        ({}, dict(), pytest.raises(TypeError), None),
        ("string", dict(), pytest.raises(TypeError), None),
    ],
)
def test_flatten_records(records, func_kwargs, expectation, expected_result):
    with expectation:
        result = flatten_records(records, **func_kwargs)
        assert result == expected_result
