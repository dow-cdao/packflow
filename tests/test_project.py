import shutil
from pathlib import Path

import pytest
from packflow.loaders.config import PackflowConfig
from packflow.project import PackflowProject


def test_packflow_project_init(tmp_path):
    """Test PackflowProject initialization"""
    project = PackflowProject(tmp_path)

    assert project.base_dir == tmp_path.resolve()


def test_has_packflow_config_true(tmp_path):
    """Test has_packflow_config returns True when packflow.yaml exists"""
    # Create a packflow.yaml
    config_file = tmp_path / "packflow.yaml"
    config_file.write_text("name: test\nversion: 0.1.0\ndescription: Test\n")

    project = PackflowProject(tmp_path)
    assert project.has_packflow_config is True


def test_has_packflow_config_false(tmp_path):
    """Test has_packflow_config returns False when packflow.yaml missing"""
    project = PackflowProject(tmp_path)
    assert project.has_packflow_config is False


def test_repr(tmp_path):
    """Test __repr__ method"""
    project = PackflowProject(tmp_path)

    repr_str = repr(project)
    assert "PackflowProject" in repr_str
    assert str(tmp_path.resolve()) in repr_str


def test_create_project(tmp_path):
    """Test creating a new packflow project"""
    import os

    original_dir = os.getcwd()

    try:
        os.chdir(tmp_path)

        project = PackflowProject.create("my_test_project")

        # Project directory should exist
        assert project.base_dir.exists()
        assert project.base_dir.name == "my_test_project"

        # Should have packflow.yaml
        assert project.has_packflow_config

        # Should have inference.py from template
        assert (project.base_dir / "inference.py").exists()

        # Should have requirements.txt
        assert (project.base_dir / "requirements.txt").exists()

        # Verify packflow.yaml content
        config = project.load_config()
        assert config.name == "my_test_project"

    finally:
        os.chdir(original_dir)


def test_create_project_with_force(tmp_path):
    """Test creating project with force=True in existing directory"""
    import os

    original_dir = os.getcwd()

    try:
        os.chdir(tmp_path)

        # Create directory first
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()

        # Create with force should work
        project = PackflowProject.create("existing_project", force=True)

        assert project.base_dir.exists()
        assert project.has_packflow_config

    finally:
        os.chdir(original_dir)


def test_create_project_without_force_fails(tmp_path):
    """Test creating project without force in existing directory fails"""
    import os

    original_dir = os.getcwd()

    try:
        os.chdir(tmp_path)

        # Create directory first
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()

        # Create without force should fail
        with pytest.raises(FileExistsError):
            PackflowProject.create("existing_project", force=False)

    finally:
        os.chdir(original_dir)


def test_load_config(tmp_path):
    """Test loading config from project"""
    # Create a packflow.yaml
    config_file = tmp_path / "packflow.yaml"
    config_file.write_text(
        """
name: test_project
version: 1.2.3
description: Test project for loading config
maintainers:
  - test@example.com

inference_backend: inference:Backend
loader: local
python_version: 3.10.0
"""
    )

    project = PackflowProject(tmp_path)
    config = project.load_config()

    assert isinstance(config, PackflowConfig)
    assert config.name == "test_project"
    assert config.version == "1.2.3"
    assert config.description == "Test project for loading config"


def test_export(tmp_path):
    """Test exporting project as zip"""
    import os

    original_dir = os.getcwd()

    try:
        os.chdir(tmp_path)

        # Create a project
        project = PackflowProject.create("export_test")

        # Export it
        zip_path = project.export(output_directory=str(tmp_path))

        # Zip should exist
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        assert "export_test" in zip_path.name

        # Verify zip contains expected files
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            names = zip_file.namelist()
            assert "packflow.yaml" in names
            assert "inference.py" in names
            assert "requirements.txt" in names

            # The zip itself should not be in the zip
            assert zip_path.name not in names

    finally:
        os.chdir(original_dir)


def test_export_to_different_directory(tmp_path):
    """Test exporting project to a different output directory"""
    import os

    original_dir = os.getcwd()

    try:
        # Create project in one directory
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        os.chdir(project_dir)

        project = PackflowProject.create("my_project")

        # Export to different directory
        export_dir = tmp_path / "exports"
        export_dir.mkdir()

        zip_path = project.export(output_directory=str(export_dir))

        # Zip should be in export_dir, not project_dir
        assert zip_path.parent == export_dir.resolve()
        assert zip_path.exists()

    finally:
        os.chdir(original_dir)


def test_export_with_version_in_filename(tmp_path):
    """Test that export filename includes version"""
    import os

    original_dir = os.getcwd()

    try:
        os.chdir(tmp_path)

        # Create project
        project = PackflowProject.create("versioned_project")

        # Modify config to have specific version
        config_file = project.base_dir / "packflow.yaml"
        config_file.write_text(
            """
name: versioned_project
version: 2.5.8
description: Test
inference_backend: inference:Backend
loader: local
"""
        )

        zip_path = project.export(output_directory=str(tmp_path))

        # Should contain version in filename
        assert "versioned_project-2.5.8.zip" == zip_path.name

    finally:
        os.chdir(original_dir)
