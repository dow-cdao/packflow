import importlib

from packflow import exceptions
from .base import InferenceBackendLoader
from .. import InferenceBackend
from .utils import inference_backend_parts


class ModuleLoader(InferenceBackendLoader):
    def load_backend_module(self) -> InferenceBackend:
        """
        Load an InferenceBackend from an installed module.

        Returns
        -------
        InferenceBackend
        """
        module_name, backend_name = inference_backend_parts(self.path)

        module = importlib.import_module(module_name)

        backend = getattr(module, backend_name, None)

        if not backend:
            raise exceptions.InferenceBackendLoadError(
                f"Backend with name `{backend_name}` does not exist in loaded module `{module}`"
            )

        return backend
