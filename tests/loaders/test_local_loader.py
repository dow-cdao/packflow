import os
from pathlib import Path

import pytest
from packflow import exceptions, InferenceBackend
from packflow.loaders import LocalLoader
from packflow.loaders.base import InferenceBackendLoader


def test_dot_notation_to_pypath():
    """Test converting dot notation to file path"""
    result = Path(LocalLoader._dot_notation_to_pypath("inference"))
    assert result.name == "inference.py"

    result = Path(LocalLoader._dot_notation_to_pypath("foo.bar"))
    assert result.parts[-2:] == ("foo", "bar.py")

    result = Path(LocalLoader._dot_notation_to_pypath("foo.bar.baz"))
    assert result.parts[-3:] == ("foo", "bar", "baz.py")


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


def test_local_loader_with_base_dir(tmp_path):
    """LocalLoader resolves paths relative to base_dir, not CWD"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "backend.py").write_text(
        """
from packflow import InferenceBackend

class Backend(InferenceBackend):
    def execute(self, inputs):
        return inputs
"""
    )

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    original = os.getcwd()
    os.chdir(cwd)

    try:
        loader = LocalLoader("backend:Backend", base_dir=project_dir)
        backend = loader.load()

        assert isinstance(backend, InferenceBackend)
        assert backend([{"test": "data"}]) == [{"test": "data"}]
    finally:
        os.chdir(original)


def test_local_loader_nested_with_base_dir(tmp_path):
    """LocalLoader resolves nested module paths relative to base_dir"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    models_dir = project_dir / "models"
    models_dir.mkdir()
    (models_dir / "__init__.py").write_text("")
    (models_dir / "backend.py").write_text(
        """
from packflow import InferenceBackend

class Backend(InferenceBackend):
    def execute(self, inputs):
        return [{"nested": True}]
"""
    )

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    original = os.getcwd()
    os.chdir(cwd)

    try:
        loader = LocalLoader("models.backend:Backend", base_dir=project_dir)
        backend = loader.load()

        assert isinstance(backend, InferenceBackend)
        assert backend([{}]) == [{"nested": True}]
    finally:
        os.chdir(original)


def test_dot_notation_to_pypath_with_base_dir(tmp_path):
    """_dot_notation_to_pypath resolves relative to base_dir"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "backend.py").write_text("")

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    original = os.getcwd()
    os.chdir(cwd)

    try:
        result = Path(
            LocalLoader._dot_notation_to_pypath("backend", base_dir=project_dir)
        )

        assert result.parent == project_dir
        assert result.name == "backend.py"
        assert result.exists()
    finally:
        os.chdir(original)


def test_from_project_with_different_cwd(tmp_path):
    """from_project passes project path to LocalLoader as base_dir"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    (project_dir / "packflow.yaml").write_text(
        """
name: test-project
version: 0.1.0
inference_backend: backend:Backend
loader: local
python_version: 3.11.0
"""
    )
    (project_dir / "backend.py").write_text(
        """
from packflow import InferenceBackend

class Backend(InferenceBackend):
    def execute(self, inputs):
        return inputs
"""
    )

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    original = os.getcwd()
    os.chdir(cwd)

    try:
        backend = InferenceBackendLoader.from_project(project_dir)

        assert isinstance(backend, InferenceBackend)
        assert backend([{"test": "data"}]) == [{"test": "data"}]
    finally:
        os.chdir(original)


def test_multiple_projects_same_session(tmp_path):
    """Load backends from multiple projects without changing CWD"""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    original = os.getcwd()
    os.chdir(cwd)

    try:
        project1 = tmp_path / "p1"
        project1.mkdir()
        (project1 / "packflow.yaml").write_text(
            """
name: p1
version: 0.1.0
inference_backend: backend:Backend
loader: local
python_version: 3.11.0
"""
        )
        (project1 / "backend.py").write_text(
            """
from packflow import InferenceBackend
class Backend(InferenceBackend):
    def execute(self, inputs):
        return [{"project": 1}]
"""
        )

        project2 = tmp_path / "p2"
        project2.mkdir()
        (project2 / "packflow.yaml").write_text(
            """
name: p2
version: 0.1.0
inference_backend: backend:Backend
loader: local
python_version: 3.11.0
"""
        )
        (project2 / "backend.py").write_text(
            """
from packflow import InferenceBackend
class Backend(InferenceBackend):
    def execute(self, inputs):
        return [{"project": 2}]
"""
        )

        backend1 = InferenceBackendLoader.from_project(project1)
        assert backend1([{}]) == [{"project": 1}]

        backend2 = InferenceBackendLoader.from_project(project2)
        assert backend2([{}]) == [{"project": 2}]
    finally:
        os.chdir(original)
