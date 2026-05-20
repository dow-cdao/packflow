import json
from typing import Any, Callable, List, Union

import packflow.exceptions as exceptions


class InferenceBackendValidator:
    def __init__(self, backend: Callable):
        self.backend = backend

    def run(self, inputs: Union[dict, List[dict]]) -> Union[dict, List[dict]]:
        """
        Run all validation checks against the backend.

        Parameters
        ----------
        inputs : Union[dict, List[dict]]
            Input data to test the backend against.

        Returns
        -------
        The validated outputs of the inference backend.
        """
        input_is_dict = isinstance(inputs, dict)
        if input_is_dict:
            inputs = [inputs]

        _input_is_correct_format(inputs)

        try:
            outputs = self.backend(inputs)
        except Exception as e:
            raise exceptions.InferenceBackendRuntimeError(
                "Error encountered when running the inference backend. This is not a validation issue. "
                "See above stack track for additional information."
            ) from e

        _inputs_and_outputs_match_len(inputs, outputs)

        _output_is_list_of_dicts(outputs)

        _output_is_json_serializable(outputs)

        _check_output_keys(
            outputs, self.backend.config.output_keys, self.backend.logger
        )

        if input_is_dict:
            outputs = outputs[0]

        return outputs


def _input_is_correct_format(inputs: Any):
    """Checks if the input is a list of dictionaries"""
    if not isinstance(inputs, list):
        raise exceptions.InferenceBackendValidationError(
            f"Production inputs will be in a list format. Input type received was {type(inputs)}"
        )

    for i, v in enumerate(inputs):
        if not isinstance(v, dict):
            raise exceptions.InferenceBackendValidationError(
                f"Value at index {i} is not a dictionary. Type found was {type(v)}"
            )


def _inputs_and_outputs_match_len(inputs: Any, outputs: Any):
    """Checks if the inputs and outputs are the same length."""

    if len(inputs) != len(outputs):
        raise exceptions.InferenceBackendValidationError(
            f"Inputs and Outputs must have matching lengths. Received {len(inputs)} inputs "
            f"and returned {len(outputs)} outputs."
        )


def _output_is_list_of_dicts(outputs: Any):
    """Checks if the output is a list of dictionaries"""
    if not isinstance(outputs, list):
        raise exceptions.InferenceBackendValidationError(
            f"Outputs must be a Python list. Input type received was {type(outputs)}"
        )

    for i, v in enumerate(outputs):
        if not isinstance(v, dict):
            raise exceptions.InferenceBackendValidationError(
                f"Outputs must be a list of dictionaries. Value at index {i} is not a dictionary. "
                f"Type found was {type(v)}"
            )


def _check_output_keys(outputs: List[dict], output_keys: List[str], logger) -> None:
    """Warns when declared output_keys are missing from actual output."""
    if not output_keys:
        return

    declared = set(output_keys)
    actual = set().union(*(record.keys() for record in outputs))

    for key in sorted(declared - actual):
        logger.warning(
            f"output_keys: declared key '{key}' was not found in any output record"
        )


def _output_is_json_serializable(outputs: Any):
    """Makes sure every row is json serializable and does not contain bad types"""
    for i, v in enumerate(outputs):
        try:
            json.dumps(v)
        except Exception as e:
            raise exceptions.InferenceBackendValidationError(
                f"Value at index {i} is not JSON Serializable. Please ensure returned values are native Python types. "
                f"Error: {e}"
            )
