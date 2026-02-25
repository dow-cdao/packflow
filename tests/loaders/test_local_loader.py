from pathlib import Path

import pytest
from packflow import exceptions
from packflow.loaders import LocalLoader


def test_dot_notation_to_pypath():
    """Test converting dot notation to file path"""
    result = LocalLoader._dot_notation_to_pypath("inference")
    assert result.endswith("inference.py")

    result = LocalLoader._dot_notation_to_pypath("foo.bar")
    assert result.endswith("foo/bar.py")

    result = LocalLoader._dot_notation_to_pypath("foo.bar.baz")
    assert result.endswith("foo/bar/baz.py")


def test_import_module_from_source():
    """Test importing a Python file as a module"""
    # Use the existing test resource
    test_file = Path(__file__).parent.parent / "resources" / "inference.py"

    module = LocalLoader._import_module_from_source(str(test_file))

    assert hasattr(module, "Backend")
    assert module.Backend.__name__ == "Backend"


def test_import_module_from_source_file_not_found():
    """Test error when file doesn't exist"""
    with pytest.raises(FileNotFoundError):
        LocalLoader._import_module_from_source("nonexistent.py")


# def test_import_module_from_source_invalid_spec(): TODO?


def test_local_loader_success(tmp_path):
    """Test successfully loading a backend from local file"""
    # Create a simple backend file
    backend_file = tmp_path / "test_backend.py"
    backend_file.write_text(
        """
from packflow import InferenceBackend

class TestBackend(InferenceBackend):
    def execute(self, inputs):
        return inputs
"""
    )

    # Change to tmp directory so relative path works
    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        loader = LocalLoader("test_backend:TestBackend")
        backend_class = loader.load_backend_module()

        assert backend_class.__name__ == "TestBackend"
    finally:
        os.chdir(original_dir)


def test_local_loader_with_load(tmp_path):
    """Test the full load() method which instantiates the backend"""
    # Create a simple backend file
    backend_file = tmp_path / "my_inference.py"
    backend_file.write_text(
        """
from packflow import InferenceBackend

class MyBackend(InferenceBackend):
    def execute(self, inputs):
        return inputs
"""
    )

    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        loader = LocalLoader("my_inference:MyBackend")
        backend = loader.load()

        # Should be instantiated
        from packflow import InferenceBackend

        assert isinstance(backend, InferenceBackend)

        # Should work
        result = backend([{"test": "data"}])
        assert result == [{"test": "data"}]
    finally:
        os.chdir(original_dir)


def test_local_loader_attribute_not_found(tmp_path):
    """Test error when backend attribute doesn't exist in module"""
    # Create a file without the expected class
    backend_file = tmp_path / "empty.py"
    backend_file.write_text("# Empty file\n")

    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        loader = LocalLoader("empty:NonExistentBackend")

        with pytest.raises(AttributeError):
            loader.load_backend_module()
    finally:
        os.chdir(original_dir)


def test_local_loader_file_not_found():
    """Test error when Python file doesn't exist"""
    loader = LocalLoader("nonexistent_module:Backend")

    with pytest.raises(exceptions.InferenceBackendLoadError) as exc_info:
        loader.load()

    assert "Unable to load inference backend module" in str(exc_info.value)
