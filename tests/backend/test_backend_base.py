from contextlib import nullcontext

import pytest

from packflow import exceptions
from packflow.backend.metrics import ExecutionMetrics

from .. import helpers


@pytest.mark.parametrize(
    "backend, expectation",
    [
        (helpers.ValidBackend, nullcontext()),
        (
            helpers.ErrorInitBackend,
            pytest.raises(exceptions.InferenceBackendInitializationError),
        ),
    ],
)
def test__inititialize(backend, expectation):
    with expectation:
        backend()


@pytest.mark.parametrize(
    "backend, expectation, inputs, expected_outputs",
    [
        (helpers.ValidBackend(), nullcontext(), {}, {}),
        (helpers.ValidBackend(), nullcontext(), [{}], [{}]),
        (
            helpers.ValidBackend(),
            pytest.raises(exceptions.InferenceBackendRuntimeError),
            5,
            None,
        ),
        (
            helpers.ErrorBackend(),
            pytest.raises(exceptions.InferenceBackendRuntimeError),
            [{}],
            None,
        ),
        (
            helpers.WrongOutputTypeBackend(),
            pytest.raises(exceptions.InferenceBackendRuntimeError),
            [{}],
            None,
        ),
    ],
)
def test_backend_call(backend, expectation, inputs, expected_outputs):
    with expectation:
        assert backend(inputs) == expected_outputs


@pytest.mark.parametrize(
    "backend, expectation, inputs, expected_outputs",
    [
        (helpers.ValidBackend(), nullcontext(), {}, {}),
        (helpers.ValidBackend(), nullcontext(), [{}], [{}]),
        (
            helpers.ErrorBackend(),
            pytest.raises(exceptions.InferenceBackendRuntimeError),
            [{}],
            None,
        ),
        (
            helpers.InvalidBackend(),
            pytest.raises(exceptions.InferenceBackendValidationError),
            [{}],
            None,
        ),
    ],
)
def test_backend_validate(backend, expectation, inputs, expected_outputs):
    with expectation:
        assert backend.validate(inputs) == expected_outputs


@pytest.mark.parametrize(
    "steps",
    [
        ["execute"],
        ["execute", "transform_outputs"],
        ["transform_inputs", "execute"],
        ["transform_inputs", "execute", "transform_outputs"],
    ],
)
def test__execute_and_profile_step(steps):
    backend = helpers.ValidBackend()
    for step in steps:
        method = getattr(backend, step)
        backend._execute_and_profile_step(method, [{}])
        assert step in backend._execution_metrics["execution_times"]
        assert isinstance(
            backend._execution_metrics["execution_times"].get(step), float
        )


@pytest.mark.parametrize("n_rows", [1, 10, 25, 50, 100])
def test_get_metrics(n_rows):
    backend = helpers.ValidBackend()
    backend([{}] * n_rows)
    backend_metrics = backend.get_metrics()
    assert backend_metrics.batch_size == n_rows
    assert isinstance(backend_metrics, ExecutionMetrics)


def test_ready():
    backend = helpers.ValidBackend()
    assert backend.ready()
