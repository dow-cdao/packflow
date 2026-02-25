from pathlib import Path
from typing import Any

import numpy as np

import packflow


TESTS_DIR = Path(__file__).parent.resolve()
RESOURCES_DIR = TESTS_DIR / "resources"


def get_resource_path(relpath: str):
    return RESOURCES_DIR.joinpath(relpath).resolve()


class ValidBackend(packflow.InferenceBackend):
    def transform_inputs(self, inputs):
        return inputs

    def execute(self, inputs: Any) -> Any:
        return inputs

    def transform_outputs(self, inputs):
        return inputs


class InvalidBackend(packflow.InferenceBackend):
    def execute(self, inputs: Any) -> Any:
        return [0]


class ErrorBackend(packflow.InferenceBackend):
    def execute(self, inputs: Any) -> Any:
        return 1 / 0


class ErrorInitBackend(packflow.InferenceBackend):
    def initialize(self) -> None:
        self.important = 1 / 0
        return

    def execute(self, inputs: Any) -> Any:
        return 1 / 0


class WrongOutputTypeBackend(packflow.InferenceBackend):
    def execute(self, inputs: Any) -> Any:
        return np.array([[0, 1]])
