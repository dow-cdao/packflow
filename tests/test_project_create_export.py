"""Tests for PackflowProject creation options and export edge cases."""

import os
import zipfile

import pytest
import packflow.project as project_module
from packflow.project import PackflowProject


@pytest.fixture
def in_tmp_path(tmp_path):
    """Run the test with cwd inside tmp_path."""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(original_dir)


@pytest.fixture
def project(in_tmp_path):
    """A freshly created project with a valid config"""
    project = PackflowProject.create("export_edge_project")
    (project.base_dir / "packflow.yaml").write_text(
        "name: export_edge_project\n"
        "version: 1.0.0\n"
        "description: Test\n"
        "inference_backend: inference:Backend\n"
        "loader: local\n"
    )
    return project


def test_create_with_optional_files_selective(in_tmp_path):
    """Only mandatory files plus requested optional files are copied"""
    project = PackflowProject.create("selective_project", optional_files=["README.md"])

    assert (project.base_dir / "inference.py").exists()
    assert (project.base_dir / "packflow.yaml").exists()
    assert (project.base_dir / "requirements.txt").exists()
    assert (project.base_dir / "README.md").exists()
    assert not (project.base_dir / "tests.py").exists()


def test_create_with_empty_optional_files(in_tmp_path):
    """An empty optional_files list copies only the mandatory files"""
    project = PackflowProject.create("mandatory_only_project", optional_files=[])

    assert (project.base_dir / "inference.py").exists()
    assert not (project.base_dir / "README.md").exists()


def test_create_with_config_data(in_tmp_path):
    """Custom config_data fields are merged into the generated config"""
    project = PackflowProject.create(
        "configured_project", config_data={"description": "custom description"}
    )

    config = project.load_config()
    assert config.description == "custom description"


def test_export_into_project_directory_excludes_archive(project):
    """Exporting into the project dir does not include the zip in itself"""
    zip_path = project.export(output_directory=str(project.base_dir))

    with zipfile.ZipFile(zip_path) as zip_file:
        names = zip_file.namelist()
    assert zip_path.name not in names


def test_create_failure_removes_new_directory(in_tmp_path, monkeypatch):
    """A failure during creation cleans up a directory we created"""

    def boom(*args, **kwargs):
        raise RuntimeError("copy failed")

    monkeypatch.setattr(project_module, "_copy_template_with_perms", boom)

    with pytest.raises(RuntimeError, match="copy failed"):
        PackflowProject.create("doomed_project")

    assert not (in_tmp_path / "doomed_project").exists()


def test_create_failure_keeps_existing_directory(in_tmp_path, monkeypatch):
    """A failure during creation leaves a pre-existing directory in place"""
    existing = in_tmp_path / "existing_project"
    existing.mkdir()
    sentinel = existing / "keep_me.txt"
    sentinel.write_text("precious")

    def boom(*args, **kwargs):
        raise RuntimeError("copy failed")

    monkeypatch.setattr(project_module, "_copy_template_with_perms", boom)

    with pytest.raises(RuntimeError):
        PackflowProject.create("existing_project", force=True)

    assert sentinel.exists()


def test_export_verbose_prints_header(project, in_tmp_path, capsys):
    """Verbose export prints the validation header and project path"""
    project.export(output_directory=str(in_tmp_path), verbose=True)

    out = capsys.readouterr().out
    assert "=== Export Validation ===" in out
    assert str(project.base_dir) in out


def test_export_blocked_by_validation_errors(project, in_tmp_path):
    """Export raises when required files are missing"""
    (project.base_dir / "requirements.txt").unlink()

    with pytest.raises(ValueError, match="Export blocked"):
        project.export(output_directory=str(in_tmp_path))


def test_export_skips_gitignored_files(project, in_tmp_path):
    """Files matched by .gitignore are excluded from the archive"""
    (project.base_dir / ".gitignore").write_text("secret.txt\n")
    (project.base_dir / "secret.txt").write_text("do not ship")

    zip_path = project.export(output_directory=str(in_tmp_path))

    with zipfile.ZipFile(zip_path) as zip_file:
        names = zip_file.namelist()
    assert "secret.txt" not in names
    assert "inference.py" in names


def test_export_skips_excluded_patterns(project, in_tmp_path):
    """Files matching default exclude patterns (e.g. *.pyc) are not exported"""
    (project.base_dir / "leftover.pyc").write_text("bytecode")

    zip_path = project.export(output_directory=str(in_tmp_path))

    with zipfile.ZipFile(zip_path) as zip_file:
        names = zip_file.namelist()
    assert "leftover.pyc" not in names


def test_export_skips_excluded_directories(project, in_tmp_path):
    """Files inside default-excluded directories are not exported"""
    cache_dir = project.base_dir / "__pycache__"
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / "module.cpython-312.pyc").write_text("bytecode")

    zip_path = project.export(output_directory=str(in_tmp_path))

    with zipfile.ZipFile(zip_path) as zip_file:
        names = zip_file.namelist()
    assert not any("__pycache__" in name for name in names)


def test_export_wraps_unexpected_errors(project, in_tmp_path, monkeypatch):
    """Unexpected failures during archiving are wrapped with context"""

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(project_module.zipfile, "ZipFile", boom)

    with pytest.raises(Exception, match="An error occurred: disk full"):
        project.export(output_directory=str(in_tmp_path))
