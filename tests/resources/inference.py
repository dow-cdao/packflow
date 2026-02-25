from typing import Any

from packflow import InferenceBackend


class Backend(InferenceBackend):
    def execute(self, inputs: Any) -> Any:
        return inputs
