from contextlib import nullcontext

import numpy as np
import pytest
from packflow import exceptions
from packflow.backend.configuration import BackendConfig
from packflow.backend.preprocessors import (
    NumpyPreprocessor,
    PassthroughPreprocessor,
    Preprocessor,
    RecordsPreprocessor,
    get_preprocessor,
)


@pytest.mark.parametrize(
    "config, expected_output",
    [
        (BackendConfig(input_format="passthrough"), PassthroughPreprocessor),
        (BackendConfig(input_format="records"), RecordsPreprocessor),
        (BackendConfig(input_format="numpy", feature_names=["foo"]), NumpyPreprocessor),
    ],
)
def test_get_preprocessor(config: BackendConfig, expected_output):
    result = get_preprocessor(config)
    assert isinstance(result, Preprocessor)
    assert isinstance(result, expected_output)


@pytest.mark.parametrize(
    "config, preprocessor_cls, expectation, inputs, expected_outputs",
    [
        # -- PASSTHROUGH PREPROCESSOR --
        (BackendConfig(), PassthroughPreprocessor, nullcontext(), [{}], [{}]),
        # -- RECORDS PREPROCESSOR --
        (BackendConfig(), RecordsPreprocessor, nullcontext(), [{}], [{}]),
        (
            BackendConfig(feature_names=["foo"]),
            RecordsPreprocessor,
            nullcontext(),
            [{"foo": 0, "bar": 1}],
            [{"foo": 0}],
        ),
        (
            BackendConfig(
                feature_names=["feature_0"],
                rename_fields={"bar": "feature_0", "foo": "feature_1"},
            ),
            RecordsPreprocessor,
            nullcontext(),
            [{"foo": 0, "bar": 1}],
            [{"feature_0": 1, "feature_1": 0}],
        ),
        (
            BackendConfig(flatten_nested_inputs=True, nested_field_delimiter=":"),
            RecordsPreprocessor,
            nullcontext(),
            [{"foo": {"bar": 0, "baz": [1]}}],
            [{"foo:bar": 0, "foo:baz": [1]}],
        ),
        (
            BackendConfig(
                flatten_nested_inputs=True,
                flatten_lists=True,
                nested_field_delimiter=":",
            ),
            RecordsPreprocessor,
            nullcontext(),
            [{"foo": {"bar": 0, "baz": [1]}}],
            [{"foo:bar": 0, "foo:baz:0": 1}],
        ),
        (
            BackendConfig(feature_names=["foo.bar"]),
            RecordsPreprocessor,
            nullcontext(),
            [{"foo": {"bar": 0, "baz": [1]}}],
            [{"foo": {"bar": 0}}],
        ),
        # -- NUMPY PREPROCESSOR --
        (
            BackendConfig(),
            NumpyPreprocessor,
            pytest.raises(exceptions.PreprocessorInitError),
            [{"foo": {"bar": 0, "baz": 1}}],
            [{"foo": {"bar": 0}}],
        ),
        (
            BackendConfig(feature_names=["foo.bar"]),
            NumpyPreprocessor,
            nullcontext(),
            [{"foo": {"bar": 0, "baz": 1}}],
            np.array([[0]]),
        ),
        (
            BackendConfig(feature_names=["foo.baz", "foo.bar"]),
            NumpyPreprocessor,
            nullcontext(),
            [{"foo": {"bar": 0, "baz": 1}}],
            np.array([[1, 0]]),
        ),
        (
            BackendConfig(
                feature_names=["feature_0"],
                rename_fields={"foo:bar": "feature_0"},
                nested_field_delimiter=":",
            ),
            NumpyPreprocessor,
            nullcontext(),
            [{"foo": {"bar": 0, "baz": 1}}],
            np.array([[0]]),
        ),
        (
            BackendConfig(feature_names=["foo"]),
            NumpyPreprocessor,
            pytest.raises(exceptions.PreprocessorRuntimeError),
            [5],
            None,
        ),
    ],
)
def test_preprocessors(config, preprocessor_cls, expectation, inputs, expected_outputs):
    with expectation:
        preprocessor = preprocessor_cls(config)
        outputs = preprocessor(inputs)
        if isinstance(outputs, np.ndarray):
            assert np.array_equal(outputs, expected_outputs)
        else:
            assert outputs == expected_outputs
