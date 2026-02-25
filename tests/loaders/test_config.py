from pathlib import Path

import pytest
import yaml
from packflow.loaders.config import PackflowConfig, load_packflow_config


def test_archive_file_name():
    """Test generating archive file name from config"""
    config = PackflowConfig(name="test_project", version="1.2.3", description="Test")

    result = config.archive_file_name("/tmp/test")

    # Use resolve() since the method resolves paths
    assert result == Path("/tmp/test/test_project-1.2.3.zip").resolve()


def test_write_yaml(tmp_path):
    """Test writing packflow.yaml with proper structure"""
    config = PackflowConfig(
        name="test_project",
        version="0.1.0",
        description="A test project",
        maintainers=["alice@example.com", "bob@example.com"],
        inference_backend="inference:Backend",
        loader="local",
        python_version="3.10.0",
    )

    yaml_path = config.write_yaml(tmp_path)

    assert yaml_path.exists()
    assert yaml_path.name == "packflow.yaml"

    # Read and verify content
    with yaml_path.open("r") as f:
        content = f.read()

    # Check sections are present
    assert "# === METADATA ===" in content
    assert "# === RUNTIME ===" in content

    # Verify data is correct
    data = yaml.safe_load(content)
    assert data["name"] == "test_project"
    assert data["version"] == "0.1.0"
    assert data["description"] == "A test project"
    assert data["maintainers"] == ["alice@example.com", "bob@example.com"]
    assert data["inference_backend"] == "inference:Backend"
    assert data["loader"] == "local"
    assert data["python_version"] == "3.10.0"


def test_write_yaml_with_custom_fields(tmp_path):
    """Test writing packflow.yaml with extra custom fields"""
    config = PackflowConfig(
        name="test_project",
        version="0.1.0",
        description="Test",
        custom_field="custom_value",
        another_custom="another_value",
    )

    yaml_path = config.write_yaml(tmp_path)

    with yaml_path.open("r") as f:
        content = f.read()

    # Custom section should be present
    assert "# === CUSTOM ===" in content

    data = yaml.safe_load(content)
    assert data["custom_field"] == "custom_value"
    assert data["another_custom"] == "another_value"


def test_write_requirements(tmp_path):
    """Test writing requirements.txt with packflow version"""
    config = PackflowConfig(name="test_project", version="0.1.0", description="Test")

    req_path = config.write_requirements(tmp_path)

    assert req_path.exists()
    assert req_path.name == "requirements.txt"

    content = req_path.read_text()
    assert content.startswith("packflow==")
    # Version should be present (exact version depends on package)
    assert "." in content  # Should have version number


def test_from_project_path_file_not_found(tmp_path):
    """Test loading config from directory without packflow.yaml raises error"""
    # Empty directory - no packflow.yaml should raise clear error
    with pytest.raises(FileNotFoundError) as exc_info:
        PackflowConfig.from_project_path(tmp_path)

    assert "Not a valid packflow project" in str(exc_info.value)


def test_load_packflow_config_success(tmp_path):
    """Test load_packflow_config function with valid project"""
    # Create a packflow.yaml
    config_file = tmp_path / "packflow.yaml"
    config_file.write_text(
        """
name: my_project
version: 1.0.0
description: Test project

inference_backend: inference:Backend
loader: local
python_version: 3.10.0
"""
    )

    config = load_packflow_config(str(tmp_path))

    assert isinstance(config, PackflowConfig)
    assert config.name == "my_project"
    assert config.version == "1.0.0"
    assert config.description == "Test project"


def test_load_packflow_config_not_found():
    """Test load_packflow_config with non-existent path"""
    with pytest.raises(NotADirectoryError) as exc_info:
        load_packflow_config("/nonexistent/path/to/project")

    assert "Could not identify packflow project" in str(exc_info.value)


def test_packflow_config_name_normalization():
    """Test that project names are normalized (hyphens to underscores)"""
    config = PackflowConfig(name="my-test-project", version="0.1.0", description="Test")

    # Hyphens should be converted to underscores
    assert config.name == "my_test_project"


def test_packflow_config_inference_backend_validation():
    """Test that inference_backend must have colon format"""
    with pytest.raises(Exception):  # Pydantic ValidationError
        PackflowConfig(
            name="test",
            version="0.1.0",
            description="Test",
            inference_backend="invalid_no_colon",
        )
