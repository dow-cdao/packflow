import pytest
from packflow import exceptions
from packflow.loaders import ModuleLoader


def test_module_loader_success():
    """Test successfully loading a backend from an installed module"""
    # Load InferenceBackend class from packflow itself
    # Ideally, we have more robust testing that has a pip installable thing with an
    # inference backend one day
    loader = ModuleLoader("packflow:InferenceBackend")
    backend_class = loader.load_backend_module()

    # Should return the class, not an instance
    assert backend_class.__name__ == "InferenceBackend"


def test_module_loader_with_load():
    """Test the full load() method which instantiates the backend"""
    # Load InferenceBackend class from packflow itself
    loader = ModuleLoader("packflow:InferenceBackend")

    # This should raise because InferenceBackend is abstract and can't be instantiated
    # Ideally, we have more robust testing that has a pip installable thing with an
    # inference backend one day
    with pytest.raises(TypeError):
        loader.load()


def test_module_loader_backend_not_found():
    """Test error when backend attribute doesn't exist in module"""
    loader = ModuleLoader("packflow:NotABackend")

    with pytest.raises(exceptions.InferenceBackendLoadError) as exc_info:
        loader.load_backend_module()

    assert "does not exist in loaded module" in str(exc_info.value)


def test_module_loader_module_not_found():
    """Test error when module doesn't exist"""
    loader = ModuleLoader("nonexistent_module:Backend")

    with pytest.raises(exceptions.InferenceBackendLoadError) as exc_info:
        loader.load()

    assert "Unable to load inference backend module" in str(exc_info.value)
