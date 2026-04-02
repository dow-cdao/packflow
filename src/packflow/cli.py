import re

import click

import packflow
from packflow.loaders.config import NAME_PATTERN


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
def export(project_path):
    """Save the package and export to .zip in the current working directory"""
    try:
        project = packflow.PackflowProject(project_path)
        output_file = project.export()
        for warning in project.export_warnings:
            _warning_message(warning)
        _success_message(f"Saved Package to {output_file}")
    except Exception as e:
        _error_message(str(e))
