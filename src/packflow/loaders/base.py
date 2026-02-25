from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from packflow import InferenceBackend, exceptions

from .config import PackflowConfig


class InferenceBackendLoader(ABC):
    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def load_backend_module(self) -> InferenceBackend:
        """
        Load the backend module from its source.
        This method should not handle instantiation or error handling, as
        it is wrapped with error handling and general validation checks at
        runtime.

        Returns
        -------
        InferenceBackend

        Notes
        -----
        The base class handles determining if the loaded object is already
        instantiated and validation checks for if the loaded object is not
        in fact an InferenceBackend object. This method should focus solely
        on loading the object from its source.
        """
        pass

    def load(self, **backend_kwargs) -> InferenceBackend:
        """
        Load the inference backend.

        Parameters
        ----------
        **backend_kwargs
            Optional Keyword arguments to pass to the backend if the provided path
            leads to a non-instantiated class.

        Returns
        -------
        InferenceBackend
            An instantiated InferenceBackend that is ready to produce inferences.
        """
        try:
            backend = self.load_backend_module()
        except Exception as e:
            raise exceptions.InferenceBackendLoadError(
                f"Unable to load inference backend module with error: {e}"
            ) from e

        if isinstance(backend, type):
            backend = backend(**backend_kwargs)

        if not isinstance(backend, InferenceBackend):
            raise exceptions.InferenceBackendLoadError(
                f"Loaded object does not appear to be a packflow InferenceBackend. Received type: {type(backend)}"
            )

        return backend

    @classmethod
    def from_project(
        cls, project_path: Union[str, Path] = ".", **backend_kwargs
    ) -> InferenceBackend:
        """Load an InferenceBackend from a Packflow directory/packflow.yaml."""
        # Prevent circular imports
        from .local import LocalLoader
        from .module import ModuleLoader

        project_path = Path(project_path).resolve()
        config = PackflowConfig.from_project_path(project_path)

        if config.loader == "local":
            loader = LocalLoader(config.inference_backend)
        elif config.loader == "module":
            loader = ModuleLoader(config.inference_backend)
        else:
            raise ValueError(f"Unknown loader type: {config.loader}")

        return loader.load(**backend_kwargs)
