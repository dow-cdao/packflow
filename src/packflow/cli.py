import re
import sys

import click

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


@click.group()
@click.version_option(version=packflow.__version__, prog_name="packflow")
def cli():
    """Command-line tools for creating, managing, and packaging Packflow inference projects."""
    pass


@cli.command()
@click.argument("project_name", type=str)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force initialization in a directory that already exists. No files will be deleted, but files may be overwritten.",
)
def create(project_name, force):
    """Initialize a new project from a template in the current working directory"""
    if not re.match(NAME_PATTERN, project_name):
        _error_message(
            f"Invalid project name '{project_name}'. "
            f"Names must start with a letter and contain only letters, digits, hyphens, and underscores."
        )
        return

    try:
        project = packflow.PackflowProject.create(project_name, force=force)
        _success_message(project)
    except Exception as e:
        _error_message(str(e))


@cli.command()
@click.argument("project_path", type=str, default=".")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed validation checks during export.",
)
def export(project_path, verbose):
    """Save the package and export to .zip in the current working directory"""
    try:
        project = packflow.PackflowProject(project_path)
        output_file = project.export(verbose=verbose)
        for warning in project.export_warnings:
            _warning_message(warning)
        _success_message(f"Saved Package to {output_file}")
    except Exception as e:
        _error_message(str(e))


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
            _success_message("All validation checks passed.")
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
