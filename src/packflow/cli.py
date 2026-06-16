import re
import subprocess
import sys

import click
import questionary

import packflow
from packflow.loaders.config import NAME_PATTERN, validate_for_export


def _success_message(msg: str):
    base = click.style("Success:", fg="green")
    click.echo(f"{base} {msg}")


def _warning_message(msg: str):
    base = click.style("Warning:", fg="yellow")
    click.echo(f"{base} {msg}")


def _error_message(msg: str):
    base = click.style("Error:", fg="red")
    click.echo(f"{base} {msg}")


def _get_git_email():
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _validate_name(name):
    if not name or not name.strip():
        return "Project name is required."
    if not re.match(NAME_PATTERN, name):
        return "Names must start with a letter and contain only letters, digits, hyphens, and underscores."
    return True


def _print_next_steps(project_name):
    click.echo()
    click.echo("  Next steps:")
    click.echo(f"    cd {project_name}")
    click.echo(
        f"    Edit inference.py {click.style('- implement the execute() method', dim=True)}"
    )
    click.echo(
        f"    packflow validate   {click.style('- check project structure', dim=True)}"
    )
    click.echo(
        f"    packflow export     {click.style('- package for distribution', dim=True)}"
    )
    click.echo()


@click.group()
@click.version_option(version=packflow.__version__, prog_name="packflow")
def cli():
    """Command-line tools for creating, managing, and packaging Packflow inference projects."""
    pass


@cli.command()
@click.argument("project_name", type=str, required=False, default=None)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force initialization in a directory that already exists. No files will be deleted, but files may be overwritten.",
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Use defaults for all prompts (for scripting and CI).",
)
def create(project_name, force, no_input):
    """Initialize a new project from a template in the current working directory.

    If PROJECT_NAME is omitted, an interactive setup wizard will guide project
    creation. Pass --no-input to skip all prompts and use default values.
    """
    interactive = sys.stdin.isatty() and not no_input

    if project_name and not re.match(NAME_PATTERN, project_name):
        _error_message(
            f"Invalid project name '{project_name}'. "
            f"Names must start with a letter and contain only letters, digits, hyphens, and underscores."
        )
        sys.exit(1)

    if interactive:
        if not project_name:
            project_name = questionary.text(
                "Project name:", validate=_validate_name
            ).ask()
            if project_name is None:
                sys.exit(1)

        description = questionary.text("Description:", default="").ask()
        if description is None:
            sys.exit(1)

        version = questionary.text("Version:", default="0.1.0").ask()
        if version is None:
            sys.exit(1)

        git_email = _get_git_email()
        maintainer = questionary.text("Maintainer email:", default=git_email).ask()
        if maintainer is None:
            sys.exit(1)

        config_data = {}
        if version:
            config_data["version"] = version
        if description:
            config_data["description"] = description
        if maintainer:
            config_data["maintainers"] = [maintainer]
    else:
        if not project_name:
            _error_message(
                "Project name is required in non-interactive mode. "
                "Usage: packflow create PROJECT_NAME [--no-input]"
            )
            sys.exit(1)
        config_data = {"version": "0.1.0"}

    try:
        project = packflow.PackflowProject.create(
            project_name, force=force, config_data=config_data
        )
        _success_message(f"Created {project_name}/")
        _print_next_steps(project_name)
    except Exception as e:
        _error_message(str(e))
        sys.exit(1)


@cli.command()
@click.argument("project_path", type=str, default=".")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed validation checks during export.",
)
def export(project_path, verbose):
    """Package the project as a distributable .zip archive."""
    try:
        project = packflow.PackflowProject(project_path)
        output_file = project.export(verbose=verbose)
        for warning in project.export_warnings:
            _warning_message(warning)
        _success_message(f"Saved Package to {output_file}")
    except Exception as e:
        _error_message(str(e))
        sys.exit(1)


@cli.command()
@click.argument("project_path", type=str, default=".")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed validation checks.",
)
@click.option(
    "--no-warnings",
    is_flag=True,
    help="Suppress warning messages.",
)
def validate(project_path, verbose, no_warnings):
    """Run all project validation checks and report results"""
    try:
        project = packflow.PackflowProject(project_path)
        config = project.load_config()

        if verbose:
            click.echo("\n=== Validation ===")
            click.echo(f"Project: {project.base_dir}")

        # Validate files (packflow.yaml validation will be integrated)
        file_errors, file_warnings = project.validate_required_files(
            verbose=verbose, config=config
        )
        errors = file_errors
        warnings = file_warnings

        # Display summary first
        if errors:
            error_count = len(errors)
            warning_count = len(warnings) if not no_warnings else 0

            if warnings and not no_warnings:
                summary = f"\n{click.style(f'{error_count} error(s)', fg='red')}, {click.style(f'{warning_count} warning(s)', fg='yellow')} found"
                click.echo(summary)
            else:
                click.echo(
                    f"\n{click.style(f'{error_count} error(s)', fg='red')} found"
                )

            click.echo()  # Blank line before individual violations

            for error in errors:
                _error_message(error)

            if not no_warnings:
                for warning in warnings:
                    _warning_message(warning)

            sys.exit(1)

        # Summary for warnings only (no errors)
        if warnings and not no_warnings:
            click.echo(
                f"\n{click.style(f'{len(warnings)} warning(s)', fg='yellow')} found"
            )
            click.echo()  # Blank line before individual violations
            for warning in warnings:
                _warning_message(warning)
            _success_message("Validation passed with warnings.")
        else:
            _success_message("All validation checks passed.")

    except Exception as e:
        _error_message(str(e))
        sys.exit(1)


@cli.command(hidden=True)
def roll():
    """Roll the box."""
    from packflow._splash import roll_in

    roll_in(force=True)
