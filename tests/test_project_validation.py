"""Tests for PackflowProject file validation and requirements checking."""

import os

import pytest
from packflow.project import PackflowProject


@pytest.fixture
def project(tmp_path):
    """A freshly created project with cwd inside tmp_path."""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield PackflowProject.create("validation_project")
    finally:
        os.chdir(original_dir)


def test_validate_verbose_all_present(project, capsys):
    """Verbose mode prints section headers and per-file checkmarks"""
    config = project.load_config()
    errors, warnings = project.validate_required_files(verbose=True, config=config)

    out = capsys.readouterr().out
    assert "Required files:" in out
    assert "Recommended files:" in out
    assert "packflow.yaml" in out
    assert "requirements.txt" in out
    assert errors == []


def test_validate_verbose_missing_required(project, capsys):
    """Missing required files are errors and marked (missing) in verbose mode"""
    (project.base_dir / "requirements.txt").unlink()
    (project.base_dir / "packflow.yaml").unlink()

    errors, warnings = project.validate_required_files(verbose=True)

    out = capsys.readouterr().out
    assert out.count("(missing)") >= 2
    assert any("packflow.yaml" in e for e in errors)
    assert any("requirements.txt" in e for e in errors)


def test_validate_verbose_missing_recommended(project, capsys):
    """Missing recommended files are warnings and marked (missing) in verbose mode"""
    (project.base_dir / "README.md").unlink()

    errors, warnings = project.validate_required_files(verbose=True)

    out = capsys.readouterr().out
    assert "README.md (missing)" in out
    assert errors == []
    assert any("README.md" in w for w in warnings)


def test_validate_requirements_without_packflow_dep(project):
    """requirements.txt lacking packflow is a validation error"""
    (project.base_dir / "requirements.txt").write_text("click>=8.0\n")

    errors, warnings = project.validate_required_files()

    assert any("'packflow' is not listed" in e for e in errors)


def test_validate_requirements_without_packflow_dep_verbose(project, capsys):
    """Verbose mode flags the missing packflow dependency inline"""
    (project.base_dir / "requirements.txt").write_text("click>=8.0\n")

    project.validate_required_files(verbose=True)

    out = capsys.readouterr().out
    assert "missing 'packflow' dependency" in out


def test_validate_recommended_file_empty(project, capsys):
    """Empty recommended files produce an 'is empty' warning"""
    (project.base_dir / "README.md").write_text("")

    errors, warnings = project.validate_required_files(verbose=True)

    out = capsys.readouterr().out
    assert any("'README.md' is empty." in w for w in warnings)
    assert "README.md (empty)" in out


def test_validate_model_card_template_placeholder(project, capsys):
    """MODEL_CARD.md still containing template placeholders is warned about"""
    (project.base_dir / "MODEL_CARD.md").write_text("# Card\n{introduction}\n")

    errors, warnings = project.validate_required_files(verbose=True)

    out = capsys.readouterr().out
    assert any(
        "'MODEL_CARD.md' appears to be unchanged from template." in w for w in warnings
    )
    assert "MODEL_CARD.md (template)" in out


def test_validate_readme_template_content(project):
    """README.md with template content is warned about"""
    (project.base_dir / "README.md").write_text("# Project Name\n")

    errors, warnings = project.validate_required_files()

    assert any(
        "'README.md' appears to be unchanged from template." in w for w in warnings
    )


def test_validate_extra_required_file_verbose(project, capsys, monkeypatch):
    """Required files without special validation get a plain verbose checkmark"""
    monkeypatch.setattr(
        PackflowProject,
        "REQUIRED_FILES",
        PackflowProject.REQUIRED_FILES + ["extra.txt"],
    )
    (project.base_dir / "extra.txt").write_text("content")

    errors, warnings = project.validate_required_files(verbose=True)

    out = capsys.readouterr().out
    assert "extra.txt" in out
    assert errors == []


# -- _validate_requirements --


def _write_requirements(project, content):
    path = project.base_dir / "requirements.txt"
    path.write_text(content)
    return path


def test_requirements_packflow_version_mismatch(project, capsys):
    """A packflow pin that excludes the installed version warns"""
    path = _write_requirements(project, "packflow==999.0.0\n")

    warnings = project._validate_requirements(path, verbose=True)

    out = capsys.readouterr().out
    assert any("packflow==999.0.0" in w for w in warnings)
    assert "packflow version mismatch" in out


def test_requirements_packflow_unpinned_verbose(project, capsys):
    """An unpinned packflow entry passes with a verbose checkmark"""
    path = _write_requirements(project, "packflow\n")

    warnings = project._validate_requirements(path, verbose=True)

    out = capsys.readouterr().out
    assert warnings == []
    assert "packflow" in out


def test_requirements_skips_comments_and_unparseable_lines(project):
    """Comments, blanks, and non-requirement lines are skipped silently"""
    path = _write_requirements(
        project, "# a comment\n\n!!!not-a-requirement!!!\npackflow\n"
    )

    warnings = project._validate_requirements(path)

    assert warnings == []


def test_requirements_installed_package_ok_verbose(project, capsys):
    """An installed package satisfying its pin gets a verbose checkmark"""
    path = _write_requirements(project, "packflow\npytest>=1.0\n")

    warnings = project._validate_requirements(path, verbose=True)

    out = capsys.readouterr().out
    assert warnings == []
    assert "pytest" in out


def test_requirements_installed_package_version_mismatch(project, capsys):
    """An installed package violating its pin warns"""
    path = _write_requirements(project, "packflow\npytest==0.0.1\n")

    warnings = project._validate_requirements(path, verbose=True)

    out = capsys.readouterr().out
    assert any("pytest" in w and "does not match" in w for w in warnings)
    assert "pytest version mismatch" in out


def test_requirements_package_not_installed(project, capsys):
    """A requirement that isn't installed in the environment warns"""
    path = _write_requirements(project, "packflow\ndefinitely-not-installed-xyz>=1.0\n")

    warnings = project._validate_requirements(path, verbose=True)

    out = capsys.readouterr().out
    assert any("definitely-not-installed-xyz" in w for w in warnings)
    assert "not installed" in out


def test_requirements_unparseable_specifier_installed(project, capsys):
    """A pin that can't be parsed as a Requirement falls back to installed-check"""
    path = _write_requirements(project, "packflow\npytest==*bad*\n")

    warnings = project._validate_requirements(path, verbose=True)

    out = capsys.readouterr().out
    assert warnings == []
    assert "pytest" in out


def test_requirements_unparseable_packflow_specifier(project, capsys):
    """A packflow pin that can't be parsed still shows a verbose checkmark"""
    path = _write_requirements(project, "packflow==*bad*\n")

    warnings = project._validate_requirements(path, verbose=True)

    out = capsys.readouterr().out
    assert warnings == []
    assert "packflow" in out


def test_validate_required_files_no_config_skips_config_checks(project):
    """Without a config object, packflow.yaml field validation is skipped"""
    errors, warnings = project.validate_required_files(config=None)

    assert errors == []
