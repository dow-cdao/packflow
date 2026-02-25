from importlib.metadata import version as _version

from .backend import BackendConfig, InferenceBackend
from .project import PackflowProject

__version__ = _version("packflow")
