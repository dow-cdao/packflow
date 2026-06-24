# Run with: pytest tests.py
# (pytest is not included in requirements.txt - install it separately)
import pytest
from packflow.loaders import LocalLoader


@pytest.fixture
def backend():
    """Load the backend as configured in packflow.yaml"""
    return LocalLoader.from_project(".")


def test_backend_loads(backend):
    """Backend initializes without error."""
    assert backend is not None


def test_check_io(backend):
    """Backend I/O passes Packflow's format checks."""
    sample_inputs = [
        {"example_field": "example_value"},
    ]
    outputs = backend.check_io(sample_inputs)
    assert outputs is not None


# def test_backend_output_values(backend):
#     """Verify specific output values for known inputs."""
#     outputs = backend([{"example_field": "example_value"}])
#     assert outputs[0]["expected_field"] == "expected_value"
