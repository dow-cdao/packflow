import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Union

import numpy as np

import packflow.exceptions as exceptions
from packflow.logger import get_logger

from .configuration import BackendConfig, load_backend_configuration
from .metrics import ExecutionMetrics
from .preprocessors import get_preprocessor
from .validation import InferenceBackendValidator


class InferenceBackend(ABC):
    """Abstract Base Class for the inference backend base"""

    backend_config_model: BackendConfig | type[BackendConfig] = BackendConfig

    def __init__(self, **kwargs):
        self.logger = get_logger()
        self.config = load_backend_configuration(self.backend_config_model, **kwargs)
        self._preprocessor = get_preprocessor(self.config)
        self._execution_metrics = dict(execution_times={})
        self._initialize()

    def __repr__(self):  # pragma: no cover
        return f"{self.__class__.__name__}[\n  {self.config.__repr__()}\n]"

    def __call__(self, inputs: Union[dict, List[dict]]) -> Union[dict, List[dict]]:
        """Execute the entire inference pipeline.

        Steps are executed in the following order:
          preprocess (internal) --> transform_inputs (optional) --> execute (required) --> transform_outputs (optional)

        Each step reports execution metrics for debugging and bottleneck identification. Metrics are logged if
        verbose=True is set in the BackendConfig. Otherwise, they can be accessed through the get_metrics() method.

        Parameters
        ----------
        inputs : Union[dict, List[dict]]
            A single dictionary or a list of dictionaries (Records) to pass through the pipeline

        Returns
        -------
        Union[dict, List[dict]]
            Object that matches the type and shape of the provided input
        """
        if not isinstance(inputs, (dict, list)):
            raise exceptions.InferenceBackendRuntimeError(
                f"Inputs must be a dictionary or Records. Type received: {type(inputs)}"
            )

        input_is_dict = isinstance(inputs, dict)

        inputs = [inputs] if input_is_dict else inputs

        self._execution_metrics["batch_size"] = len(inputs)

        preprocessed = self._execute_and_profile_step(self._preprocess, inputs)

        if hasattr(self, "transform_inputs"):
            features = self._execute_and_profile_step(
                self.transform_inputs, preprocessed
            )
        else:
            features = preprocessed

        results = self._execute_and_profile_step(self.execute, features)

        if hasattr(self, "transform_outputs"):
            outputs = self._execute_and_profile_step(self.transform_outputs, results)
        else:
            outputs = results

        if not isinstance(outputs, list):
            raise exceptions.InferenceBackendRuntimeError(
                f"Output of inference backend is not a list. Received type: {type(outputs)}"
            )

        if input_is_dict:
            outputs = outputs[0]

        if self.config.verbose:
            self.logger.info(f"{self.get_metrics().__repr__()}")

        return outputs

    def _initialize(self):
        """Metrics wrapper for user-defined initialize function"""
        start = time.perf_counter()
        try:
            self.initialize()
        except Exception as e:
            raise exceptions.InferenceBackendInitializationError(
                f"Failed to initialize inference backend: {e}"
            ) from e

        delta = time.perf_counter() - start

        if self.config.verbose:
            self.logger.info(
                f"Initialized {self.__class__.__name__} in {delta:,.4f} ms"
            )

    def _preprocess(self, raw_inputs: List[dict]) -> Union[List[dict], "np.array"]:
        """
        Run the internally configured data preprocessor
        """
        return self._preprocessor(raw_inputs)

    def _execute_and_profile_step(self, method: Callable, data: Any) -> Any:
        """
        Wrap execution of a method with error handling and gather execution time.

        Parameters
        ----------
        method: Callable
            The method to execute

        data: Any
            The input data for the step

        Returns
        -------
        Any
            The output of the step

        Notes
        -----
        This method is not a decorator because subclasses will override the main methods
        (transform_inputs, execute, transform_outputs), and would require users to manually
        specify the decorator at development time. This approach removes that concern and
        reduces redundant code.
        """
        name = method.__name__.strip("_")
        start = time.perf_counter()

        try:
            result = method(data)
        except Exception as e:
            raise exceptions.InferenceBackendRuntimeError(
                f"{name}() failed with the following error: {e}"
            ) from e

        time_ms = (time.perf_counter() - start) * 1000

        self._execution_metrics["execution_times"][name] = round(time_ms, 5)

        return result

    def initialize(self) -> None:
        """User-defined initialization steps. Runs during __init__ for the base class.

        Notes
        -----
        This function is to simplify initialization steps for an extension of this class
        """
        return

    # def transform_inputs(self, inputs: Union[List[dict], Any]) -> Any:
    #     """Preprocessing steps or other transformations before running inference.
    #
    #     This function should ingest raw records and return inference-ready features.
    #     Ex: [{"foo": 5}] -> np.array([[5]])
    #
    #     Parameters
    #     ----------
    #     inputs: List[Dict]
    #         A list of dictionary objects
    #
    #     Returns
    #     -------
    #     Any
    #         The expected input data for the model or function is.
    #
    #     Notes
    #     -----
    #     This function should *not* filter rows. The input and output batches should
    #     have the same length.
    #     """
    #     return inputs

    @abstractmethod
    def execute(self, inputs: Any) -> Any:  # pragma: no cover
        """The main execution of inference or analysis for the developed application.

        This method should remain targeted to passing data through the model/execution
        code for profiling purposes. Minimal pre- or post-processing should occur at this
        step unless completely necessary.

        Parameters
        ----------
        inputs: List[Dict]
            The output of the transform_inputs method. If the transform_inputs method is
            not overridden, the data is formatted as records (list of dictionaries)

        Returns
        -------
        Any
            Model Outputs

        Notes
        -----
        The transform_outputs() method should handle all postprocessing including calculating
        metrics, converting outputs back to Python types, and other postprocessing steps. Try
        to keep this method focused purely on inference/analysis.
        """
        pass

    # def transform_outputs(self, outputs: Any) -> List[dict]:
    #     """The main execution of inference or
    #
    #     This method should remain targeted to passing data through the model/execution
    #     code for profiling purposes. Minimal
    #
    #     Parameters
    #     ----------
    #     outputs: Any
    #         The output of the transform_inputs method. If the transform_inputs method is
    #         not overridden, the data is formatted as records (list of dictionaries)
    #
    #     Returns
    #     -------
    #     List[dict]
    #         Model Outputs
    #
    #     Notes
    #     -----
    #     The transform_outputs() method *must* output json-serializable data in the form of
    #     records (a list of dictionaries).
    #     """
    #     return outputs

    def validate(self, inputs: Union[dict, List[dict]]) -> Union[dict, List[dict]]:
        """
        Run validations against the inference backend to ensure it meets API restrictions
        """
        validator = InferenceBackendValidator(self)

        return validator.run(inputs)

    def get_metrics(self) -> ExecutionMetrics:
        """
        Utility for collecting user-defined metrics and validating their contents

        Returns
        -------
        ExecutionMetrics
        """
        return ExecutionMetrics(**self._execution_metrics)

    def ready(self) -> bool:
        """
        Optional function to define when the app is ready to execute

        Returns
        -------
        bool
        """
        return self is not None
