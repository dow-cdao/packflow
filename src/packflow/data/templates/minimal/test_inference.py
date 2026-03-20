# A starting point for testing the Inference Backend with pytest. The fixture below handles loading the backend
# from packflow.yaml - add test cases to verify the backend behaves as expected for this analytic.
import pytest
from packflow.loaders import LocalLoader


@pytest.fixture
def backend():
    """Load the backend as configured in packflow.yaml"""
    return LocalLoader.from_project(".")


def test_backend_loads(backend):
    """Backend initializes without error."""
    assert backend is not None


# Uncomment and add input data to test backend behavior.
# def test_backend_validate(backend):
#     sample_inputs = [
#         {"example_field": "example_value"},
#     ]
#     outputs = backend.validate(sample_inputs)
#     assert outputs is not None
#
# def test_backend_output_values(backend):
#     outputs = backend([{"example_field": "example_value"}])
#     assert outputs[0]["expected_field"] == "expected_value"
