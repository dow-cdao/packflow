import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from .base import InferenceBackendLoader
from .. import InferenceBackend
from .utils import inference_backend_parts


class LocalLoader(InferenceBackendLoader):
    @staticmethod
    def _dot_notation_to_pypath(path: str) -> str:
        """
        Convert a dotted-path like 'foo.bar' to a file path to a python module

        Parameters
        ----------
        path : str
            The path to the module in dot notation

        """
        module = path.replace(".", "/")

        return str(Path(module).with_suffix(".py").resolve())

    @staticmethod
    def _import_module_from_source(path: str) -> ModuleType:
        """
        Load a Python module from a local file path.
        """
        source_path = Path(path).resolve(strict=True)

        spec = importlib.util.spec_from_file_location(source_path.stem, source_path)

        if not spec:
            raise ImportError(f"Unable to import Python script from: {path}")

        module = importlib.util.module_from_spec(spec)

        sys.modules[spec.name] = module

        spec.loader.exec_module(module)

        return module

    def load_backend_module(self, **backend_kwargs) -> InferenceBackend:
        module_name, obj_name = inference_backend_parts(self.path)

        module_path = self._dot_notation_to_pypath(module_name)

        module = self._import_module_from_source(module_path)

        backend = getattr(module, obj_name)

        return backend
