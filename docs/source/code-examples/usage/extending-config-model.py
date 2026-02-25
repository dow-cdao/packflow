from typing import Any, List

from packflow import BackendConfig, InferenceBackend


class CustomConfigModel(BackendConfig):
    # New domain-specific fields with defaults
    model_path: str = "./resources/model.joblib"

    # Set fields without defaults so the backend cannot start without this provided
    output_class_names: list[str]


class CustomBackend(InferenceBackend):
    backend_config_model = CustomConfigModel

    def initialize(self):
        self.logger(f"Loading model from {self.config.model_path}")
        self.model = lambda x: x  # Mocking loading of a model

    def execute(self, inputs: Any) -> Any:
        return self.model(inputs)

    def transform_outputs(self, outputs: Any) -> List[dict]:
        cleaned = []
        for row in outputs:
            cleaned.append(dict(zip(self.config.output_class_names, row)))
        return cleaned
