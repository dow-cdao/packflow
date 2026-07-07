"""Tests for the interactive create wizard and CLI helper/error paths."""

import os

import pytest
from click.testing import CliRunner

import packflow._splash
import packflow.cli as cli_module
from packflow.cli import _get_git_email, _validate_name, cli


@pytest.fixture
def runner():
    """Fixture for invoking Click commands"""
    return CliRunner()


@pytest.fixture
def in_tmp_path(tmp_path):
    """Run the test with cwd inside tmp_path."""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(original_dir)


class _FakeQuestion:
    def __init__(self, answer):
        self.answer = answer

    def ask(self):
        return self.answer


@pytest.fixture
def interactive(monkeypatch):
    """Force the interactive path and stub out the splash animation.

    Returns a function that queues answers for successive questionary prompts.
    CliRunner replaces sys.stdin during invoke, so the tty check is forced by
    stubbing the sys reference inside the cli module instead.
    """
    import sys
    from types import SimpleNamespace

    fake_sys = SimpleNamespace(
        stdin=SimpleNamespace(isatty=lambda: True), exit=sys.exit
    )
    monkeypatch.setattr(cli_module, "sys", fake_sys)
    monkeypatch.setattr(packflow._splash, "roll_in", lambda force=False: None)

    def queue_answers(*answers):
        answer_iter = iter(answers)

        def fake_text(prompt, default="", validate=None):
            return _FakeQuestion(next(answer_iter))

        monkeypatch.setattr(cli_module.questionary, "text", fake_text)

    return queue_answers


def test_interactive_create_prompts_for_name(runner, in_tmp_path, interactive):
    """With no name argument, the wizard prompts for all fields"""
    interactive("wizard_project", "A description", "1.2.3", "dev@example.com")

    result = runner.invoke(cli, ["create"])

    assert result.exit_code == 0
    assert "New Packflow Project" in result.output
    assert (in_tmp_path / "wizard_project" / "packflow.yaml").exists()
    config_text = (in_tmp_path / "wizard_project" / "packflow.yaml").read_text()
    assert "1.2.3" in config_text
    assert "dev@example.com" in config_text


def test_interactive_create_with_name_argument(runner, in_tmp_path, interactive):
    """With a name argument, the wizard shows it and prompts for the rest"""
    interactive("", "0.1.0", "")

    result = runner.invoke(cli, ["create", "named_project"])

    assert result.exit_code == 0
    assert "named_project" in result.output
    assert (in_tmp_path / "named_project" / "packflow.yaml").exists()


def test_interactive_create_cancelled_at_name(runner, in_tmp_path, interactive):
    """Cancelling the name prompt (ctrl-c -> None) exits nonzero"""
    interactive(None)

    result = runner.invoke(cli, ["create"])

    assert result.exit_code == 1


def test_interactive_create_cancelled_at_description(runner, in_tmp_path, interactive):
    """Cancelling a later prompt exits nonzero"""
    interactive("cancelled_project", None)

    result = runner.invoke(cli, ["create"])

    assert result.exit_code == 1


def test_interactive_create_cancelled_at_version(runner, in_tmp_path, interactive):
    """Cancelling the version prompt exits nonzero"""
    interactive("cancelled_project", "desc", None)

    result = runner.invoke(cli, ["create"])

    assert result.exit_code == 1


def test_interactive_create_cancelled_at_maintainer(runner, in_tmp_path, interactive):
    """Cancelling the maintainer prompt exits nonzero"""
    interactive("cancelled_project", "desc", "1.0.0", None)

    result = runner.invoke(cli, ["create"])

    assert result.exit_code == 1


def test_create_rejects_invalid_project_name(runner, in_tmp_path):
    """An invalid project name argument errors before any prompting"""
    result = runner.invoke(cli, ["create", "1-bad-name"])

    assert result.exit_code == 1
    assert "Invalid project name" in result.output


def test_create_no_input_requires_name(runner, in_tmp_path):
    """Non-interactive mode without a project name is an error"""
    result = runner.invoke(cli, ["create", "--no-input"])

    assert result.exit_code == 1
    assert "Project name is required" in result.output


# -- helpers --


def test_validate_name_helper():
    """_validate_name returns messages for bad names and True for good ones"""
    assert _validate_name("") == "Project name is required."
    assert _validate_name("   ") == "Project name is required."
    assert "must start with a letter" in _validate_name("1bad")
    assert _validate_name("good_name") is True


def test_get_git_email_returns_string():
    """_get_git_email returns a string from git config"""
    email = _get_git_email()

    assert isinstance(email, str)


def test_get_git_email_handles_failure(monkeypatch):
    """_get_git_email returns empty string when git is unavailable"""

    def boom(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr(cli_module.subprocess, "run", boom)

    assert _get_git_email() == ""


# -- validate command paths --


def _make_valid_project(runner, name="clean_project"):
    result = runner.invoke(cli, ["create", name, "--no-input"])
    assert result.exit_code == 0
    return name


def test_validate_verbose_header(runner, in_tmp_path):
    """validate -v prints the validation header"""
    name = _make_valid_project(runner)

    result = runner.invoke(cli, ["validate", name, "-v"])

    assert "=== Validation ===" in result.output


def test_validate_errors_with_no_warnings_flag(runner, in_tmp_path):
    """validate --no-warnings shows only the error count on failure"""
    name = _make_valid_project(runner)
    (in_tmp_path / name / "requirements.txt").unlink()

    result = runner.invoke(cli, ["validate", name, "--no-warnings"])

    assert result.exit_code == 1
    assert "error(s)" in result.output
    assert "warning(s)" not in result.output


def test_validate_all_checks_passed(runner, in_tmp_path, monkeypatch):
    """A fully clean project reports that all checks passed"""
    import yaml

    name = _make_valid_project(runner)
    project_dir = in_tmp_path / name

    config = yaml.safe_load((project_dir / "packflow.yaml").read_text())
    config["description"] = "A complete project"
    config["maintainers"] = ["dev@example.com"]
    (project_dir / "packflow.yaml").write_text(yaml.safe_dump(config))
    (project_dir / "README.md").write_text("Real, bespoke documentation.\n")
    (project_dir / "MODEL_CARD.md").write_text("A real model card.\n")
    (project_dir / "LICENSE.txt").write_text("MIT License\n")

    result = runner.invoke(cli, ["validate", name])

    assert result.exit_code == 0, result.output
    assert "All validation checks passed." in result.output


def test_validate_nonexistent_project_errors(runner, in_tmp_path):
    """validate on a directory without packflow.yaml errors out"""
    result = runner.invoke(cli, ["validate", "no_such_dir"])

    assert result.exit_code == 1
    assert "Error:" in result.output


def test_roll_command(runner, monkeypatch):
    """The hidden roll command invokes the splash animation"""
    calls = []
    monkeypatch.setattr(
        packflow._splash, "roll_in", lambda force=False: calls.append(force)
    )

    result = runner.invoke(cli, ["roll"])

    assert result.exit_code == 0
    assert calls == [True]
