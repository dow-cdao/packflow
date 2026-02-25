import click

import packflow


def _success_message(msg: str):
    base = click.style("Success:", fg="green")
    click.echo(f"{base} {msg}")


def _error_message(msg: str):
    base = click.style("Error:", fg="red")
    click.echo(f"{base} {msg}")


@click.group()
def cli():
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
        _success_message(f"Saved Package to {output_file}")
    except Exception as e:
        _error_message(str(e))
