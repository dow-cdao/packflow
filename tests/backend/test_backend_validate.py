from contextlib import nullcontext

import numpy as np
import packflow.exceptions as exceptions
import pytest
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


def _loguru_sink():
    """Returns a (buffer, sink_id) pair for capturing loguru output in tests."""
    import io

    from loguru import logger

    buf = io.StringIO()
    sid = logger.add(buf, level="WARNING", format="{message}")
    return buf, sid


def test__check_output_keys_no_warning_when_not_declared():
    """No warnings when output_keys is empty (declarative field not set)."""
    from loguru import logger
    from packflow.logger import get_logger

    buf, sid = _loguru_sink()
    try:
        validation._check_output_keys([{"score": 0.9}], [], get_logger())
    finally:
        logger.remove(sid)
    assert "output_keys" not in buf.getvalue()


def test__check_output_keys_no_warning_when_match():
    """No warnings when output records match declared keys exactly."""
    from loguru import logger
    from packflow.logger import get_logger

    buf, sid = _loguru_sink()
    try:
        validation._check_output_keys(
            [{"score": 0.9, "label": "A"}, {"score": 0.1, "label": "B"}],
            ["score", "label"],
            get_logger(),
        )
    finally:
        logger.remove(sid)
    assert "output_keys" not in buf.getvalue()


def test__check_output_keys_warns_missing_key():
    """Warns when a declared key is absent from all output records."""
    from loguru import logger
    from packflow.logger import get_logger

    buf, sid = _loguru_sink()
    try:
        validation._check_output_keys(
            [{"score": 0.9}], ["score", "label"], get_logger()
        )
    finally:
        logger.remove(sid)
    assert "'label' was not found" in buf.getvalue()


def test__check_output_keys_no_warning_for_extra_keys():
    """No warnings when output records contain keys not in output_keys."""
    from loguru import logger
    from packflow.logger import get_logger

    buf, sid = _loguru_sink()
    try:
        validation._check_output_keys(
            [{"score": 0.9, "debug_info": "x"}], ["score"], get_logger()
        )
    finally:
        logger.remove(sid)
    assert "output_keys" not in buf.getvalue()
