from pathlib import Path

import pytest
from packflow import InferenceBackend, exceptions
from packflow.loaders import LocalLoader
from packflow.loaders.base import InferenceBackendLoader
from pydantic import ValidationError


def test_load_returns_non_backend_error(tmp_path: Path):
    """Test error when loaded object is not an InferenceBackend"""
    # Create a file with a non-backend class
    backend_file = tmp_path / "not_backend.py"
    backend_file.write_text(
        """
class NotABackend:
    pass
"""
    )

    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        loader = LocalLoader("not_backend:NotABackend")

        with pytest.raises(exceptions.InferenceBackendLoadError) as exc_info:
            loader.load()

    finally:
        os.chdir(original_dir)


def test_load_with_already_instantiated_backend(tmp_path):
    """Test that load() works when backend module returns an instance"""
    # Create a file with an already-instantiated backend
    backend_file = tmp_path / "instance_backend.py"
    backend_file.write_text(
        """
from packflow import InferenceBackend

class MyBackend(InferenceBackend):
    def execute(self, inputs):
        return inputs

# Export an instance, not the class
backend_instance = MyBackend()
"""
    )

    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        loader = LocalLoader("instance_backend:backend_instance")
        backend = loader.load()

        # Should return the instance as-is, so no need to call load()
        assert isinstance(backend, InferenceBackend)
        result = backend([{"test": "data"}])
        assert result == [{"test": "data"}]
    finally:
        os.chdir(original_dir)


def test_from_project_with_local_loader(tmp_path: Path):
    """Test loading a backend from a project directory with local loader"""
    # Create a packflow.yaml
    packflow_yaml = tmp_path / "packflow.yaml"
    packflow_yaml.write_text(
        """
name: test_project
version: 0.0.1
description: Test project
maintainers:
 - test@example.com

inference_backend: inference:Backend
loader: local
python_version: 3.10.0
"""
    )

    # Create the backend file
    backend_file = tmp_path / "inference.py"
    backend_file.write_text(
        """
from packflow import InferenceBackend

class Backend(InferenceBackend):
    def execute(self, inputs):
        return inputs
"""
    )
    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Use from_project class method
        backend = InferenceBackendLoader.from_project(".")

        assert isinstance(backend, InferenceBackend)
        result = backend([{"test": "data"}])
        assert result == [{"test": "data"}]
    finally:
        os.chdir(original_dir)


def test_from_project_with_module_loader(tmp_path):
    """Test loading a backend from a project directory with module loader"""
    # Create a packflow.yaml with module loader
    config_file = tmp_path / "packflow.yaml"
    config_file.write_text(
        """
name: test-project
version: 0.1.0
description: Test project
maintainers:
  - test@example.com

# Ideally, we have more robust testing that has a pip installable thing
# with an inference backend one day
inference_backend: packflow:InferenceBackend
loader: module
python_version: 3.10.0
"""
    )

    # This will try to load InferenceBackend from packflow (which is abstract)
    # Should raise TypeError when trying to instantiate
    with pytest.raises(TypeError):
        InferenceBackendLoader.from_project(tmp_path)


def test_from_project_unknown_loader_type(tmp_path):
    """Test error when packflow.yaml specifies unknown loader type"""
    # Create a packflow.yaml with invalid loader
    config_file = tmp_path / "packflow.yaml"
    config_file.write_text(
        """
name: test-project
version: 0.1.0
description: Test project

inference_backend: inference:Backend
loader: unknown_loader_type
python_version: 3.10.0
"""
    )

    # Pydantic validation catches this before it reaches the ValueError
    with pytest.raises(ValidationError) as exc_info:
        InferenceBackendLoader.from_project(tmp_path)

    assert "Input should be 'local' or 'module'" in str(exc_info.value)


def test_load_with_backend_kwargs(tmp_path):
    """Test that backend_kwargs are passed through to backend initialization"""
    # Create a backend that accepts kwargs
    backend_file = tmp_path / "kwargs_backend.py"
    backend_file.write_text(
        """
from packflow import InferenceBackend

class KwargsBackend(InferenceBackend):
    def __init__(self, custom_param=None, **kwargs):
        self.custom_param = custom_param
        super().__init__(**kwargs)

    def execute(self, inputs):
        return inputs
"""
    )

    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        loader = LocalLoader("kwargs_backend:KwargsBackend")
        backend = loader.load(custom_param="test_value")

        assert backend.custom_param == "test_value"
    finally:
        os.chdir(original_dir)
