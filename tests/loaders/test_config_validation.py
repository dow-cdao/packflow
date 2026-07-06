"""Tests for validate_for_export, check_python_version, and write_yaml sections."""

import os

import pytest
from packflow.loaders.config import (
    PackflowConfig,
    check_python_version,
    get_python_version,
    validate_for_export,
)
from packflow.project import PackflowProject


@pytest.fixture
def project(tmp_path):
    """A created project with full metadata and a runtime-matching python version"""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield PackflowProject.create(
            "config_validation_project",
            config_data={
                "description": "A test project",
                "maintainers": ["dev@example.com"],
                "python_version": get_python_version(),
            },
        )
    finally:
        os.chdir(original_dir)


def test_validate_for_export_verbose_happy_path(project, capsys):
    """Verbose validation prints checkmarks for every metadata/runtime field"""
    config = project.load_config()

    errors, warnings = validate_for_export(
        config, project_dir=project.base_dir, verbose=True
    )

    out = capsys.readouterr().out
    assert errors == []
    assert "Metadata:" in out
    assert "name: config_validation_project" in out
    assert "version: 0.1.0" in out
    assert "description: A test project" in out
    assert "maintainers: dev@example.com" in out
    assert "Runtime:" in out
    assert "inference_backend: inference:Backend" in out
    assert "inference.py" in out
    assert "loader: local" in out
    assert "(matches runtime)" in out
    assert "Smoke tests:" in out
    assert "LocalLoader succeeded" in out
    assert "InferenceBackendLoader.from_project succeeded" in out


def test_validate_for_export_long_description_truncated(project, capsys):
    """Descriptions over 50 characters are truncated in verbose output"""
    config = project.load_config()
    config.description = "x" * 80

    validate_for_export(config, project_dir=project.base_dir, verbose=True)

    out = capsys.readouterr().out
    assert ("x" * 50 + "...") in out
    assert ("x" * 51) not in out


def test_validate_for_export_empty_name_and_version(project):
    """Empty name and version are blocking errors"""
    config = project.load_config()
    config.name = ""
    config.version = "  "

    errors, warnings = validate_for_export(config, project_dir=project.base_dir)

    assert any("'name' is required" in e for e in errors)
    assert any("'version' is required" in e for e in errors)


def test_validate_for_export_missing_backend_file_verbose(project, capsys):
    """A missing inference backend file is an error and marked in verbose mode"""
    (project.base_dir / "inference.py").unlink()
    config = project.load_config()

    errors, warnings = validate_for_export(
        config, project_dir=project.base_dir, verbose=True
    )

    out = capsys.readouterr().out
    assert any("Inference backend file 'inference.py' is missing" in e for e in errors)
    assert "inference.py (missing)" in out
    assert any("failed" in e for e in errors)


def test_validate_for_export_module_loader_success(project, capsys):
    """Module loader mode smoke-tests the importable backend"""
    config = project.load_config()
    config.loader = "module"
    config.inference_backend = "packflow:InferenceBackend"

    errors, warnings = validate_for_export(
        config, project_dir=project.base_dir, verbose=True
    )

    out = capsys.readouterr().out
    assert "ModuleLoader.load()" in out
    assert "ModuleLoader succeeded" in out


def test_validate_for_export_module_loader_failure(project, capsys):
    """A module backend that can't be imported formats a module-mode error"""
    config = project.load_config()
    config.loader = "module"
    config.inference_backend = "packflow:NotABackend"

    errors, warnings = validate_for_export(
        config, project_dir=project.base_dir, verbose=True
    )

    out = capsys.readouterr().out
    assert "ModuleLoader failed" in out
    assert any("failed ModuleLoader test (configured mode)" in e for e in errors)


def test_validate_for_export_from_project_failure(tmp_path, capsys):
    """from_project smoke test failure is reported as a generic smoke-test error"""
    config = PackflowConfig(name="no_such_project")

    errors, warnings = validate_for_export(config, project_dir=tmp_path, verbose=True)

    out = capsys.readouterr().out
    assert "InferenceBackendLoader.from_project failed" in out
    assert any("failed smoke test" in e for e in errors)


def test_validate_for_export_no_project_dir_skips_smoke_tests(project, capsys):
    """Without a project_dir, backend file checks and smoke tests are skipped"""
    config = project.load_config()

    errors, warnings = validate_for_export(config, project_dir=None, verbose=True)

    out = capsys.readouterr().out
    assert errors == []
    assert "Smoke tests:" not in out


def test_validate_for_export_python_mismatch_warning(project):
    """A python_version mismatch surfaces as an export warning"""
    config = project.load_config()
    config.python_version = "2.7.0"

    errors, warnings = validate_for_export(config, project_dir=project.base_dir)

    assert any("packflow.yaml specifies Python 2.7.0" in w for w in warnings)


def test_check_python_version_unparsable(project):
    """An unparsable python_version yields a parse warning"""
    config = project.load_config()
    config.python_version = "banana"

    warning = check_python_version(config)

    assert "Could not parse python_version 'banana'" in warning


def test_check_python_version_mismatch(project):
    """A minor-version mismatch yields an update-recommendation warning"""
    config = project.load_config()
    config.python_version = "2.7.0"

    warning = check_python_version(config)

    assert "packflow.yaml specifies Python 2.7.0" in warning


def test_write_yaml_includes_optional_sections(tmp_path):
    """env, backend_config, and extra sections are written when populated"""
    config = PackflowConfig(
        name="sectioned",
        env={"KEY": "value"},
        backend_config={"threshold": 0.5},
        extra={"custom": True},
    )

    path = config.write_yaml(tmp_path)

    content = path.read_text()
    assert "# === ENVIRONMENT ===" in content
    assert "# === BACKEND CONFIG ===" in content
    assert "# === CUSTOM ===" in content
