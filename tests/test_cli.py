import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from packflow.cli import cli


@pytest.fixture
def runner():
    """Fixture for invoking Click commands"""
    return CliRunner()


def test_create_command_success(runner: CliRunner, tmp_path: Path):
    """Test `packflow create` command successfully creates a project"""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        result = runner.invoke(cli, ["create", "test_project"])

        assert result.exit_code == 0
        # Verify file structure exists
        to_verify = [
            tmp_path / "test_project",
            tmp_path / "test_project" / "packflow.yaml",
            tmp_path / "test_project" / "requirements.txt",
            tmp_path / "test_project" / "LICENSE.txt",
            tmp_path / "test_project" / "README.md",
            tmp_path / "test_project" / "MODEL_CARD.md",
            tmp_path / "test_project" / "inference.py",
            tmp_path / "test_project" / "validate.py",
        ]
        for path in to_verify:
            assert path.exists()
        assert "Success:" in result.output

    finally:
        os.chdir(original_dir)


def test_create_command_failure(runner, tmp_path):
    """Test packflow create command handles errors"""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Create directory first
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()

        # Should fail without --force
        result = runner.invoke(cli, ["create", "existing_project"])

        assert result.exit_code == 0  # Click doesn't exit non-zero by default
        assert "Error:" in result.output

    finally:
        os.chdir(original_dir)


def test_export_command_success(runner: CliRunner, tmp_path: Path):
    """Test `packflow export` command successfully exports a project"""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        # First create a project
        runner.invoke(cli, ["create", "export_test"])

        project_dir = tmp_path / "export_test"
        os.chdir(project_dir)

        # Export it
        result = runner.invoke(cli, ["export", "."])

        assert result.exit_code == 0
        assert "Success:" in result.output
        assert "Saved Package to" in result.output
        assert ".zip" in result.output

        # Verify zip was created
        zip_files = list(project_dir.glob("*.zip"))
        assert len(zip_files) == 1

    finally:
        os.chdir(original_dir)


def test_export_command_default_path(runner, tmp_path):
    """Test packflow export uses current directory by default"""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Create a project
        runner.invoke(cli, ["create", "default_export"])

        project_dir = tmp_path / "default_export"
        os.chdir(project_dir)

        # Export without specifying path (should default to ".")
        result = runner.invoke(cli, ["export"])

        assert result.exit_code == 0
        assert "Success:" in result.output

    finally:
        os.chdir(original_dir)


def test_export_command_failure(runner, tmp_path):
    """Test packflow export command handles errors"""
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Try to export non-existent project
        result = runner.invoke(cli, ["export", "nonexistent_project"])

        assert result.exit_code == 0
        assert "Error:" in result.output

    finally:
        os.chdir(original_dir)


def test_cli_group_exists(runner):
    """Test that CLI group is accessible"""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "create" in result.output
    assert "export" in result.output


def test_create_help(runner):
    """Test create command help"""
    result = runner.invoke(cli, ["create", "--help"])

    assert result.exit_code == 0
    assert "Initialize a new project" in result.output
    assert "--force" in result.output


def test_export_help(runner):
    """Test export command help"""
    result = runner.invoke(cli, ["export", "--help"])

    assert result.exit_code == 0
    assert "Save the package" in result.output
