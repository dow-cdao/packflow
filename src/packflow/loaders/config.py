import sys
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

import click
import yaml
from pydantic import BaseModel, ConfigDict, StringConstraints

import packflow.constants as constants

METADATA_KEYS = ["name", "version", "description", "maintainers"]
RUNTIME_CONFIG_KEYS = ["inference_backend", "loader", "python_version"]


def get_python_version():
    """
    Extract semantic version of the current process' python
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


NAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_-]*$"

NameStr = Annotated[str, StringConstraints(pattern=NAME_PATTERN)]

InferenceBackendStr = Annotated[str, StringConstraints(pattern=r"^[^:]+:[^:]+$")]


def normalize_archive_name(name: str) -> str:
    """Normalize a project name for use in archive filenames (PEP 625).

    Hyphens are replaced with underscores so that the hyphen in the
    archive filename unambiguously separates the name from the version.
    """
    return name.replace("-", "_")


class PackflowConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: NameStr
    version: str = ""
    description: str = ""
    maintainers: list[str] = []

    inference_backend: InferenceBackendStr = "inference:Backend"
    loader: Literal["local", "module"] = "local"
    python_version: str = get_python_version()

    @classmethod
    def from_project_path(cls, base_dir: Union[str, Path]):
        config = _load_raw_packaging_config(base_dir)
        return cls(**config)

    def archive_file_name(self, base_dir: Union[str, Path]):
        base_dir = Path(base_dir).resolve()
        return base_dir / f"{normalize_archive_name(self.name)}-{self.version}.zip"

    def write_yaml(self, base_dir: Union[str, Path]):
        base_dir = Path(base_dir).resolve()
        packaging_config = base_dir / constants.PACKAGING_CONFIG_NAME

        with packaging_config.open("w+") as f:
            # Preserve order and comment structure
            config_data = self.model_dump()
            f.write("# === METADATA ===\n")
            yaml.safe_dump(
                {k: config_data[k] for k in METADATA_KEYS if k in config_data},
                f,
                sort_keys=False,
            )
            f.write("\n# === RUNTIME ===\n")
            yaml.safe_dump(
                {k: config_data[k] for k in RUNTIME_CONFIG_KEYS if k in config_data},
                f,
                sort_keys=False,
            )
            remaining_fields = list(
                set(config_data.keys()) - set(METADATA_KEYS) - set(RUNTIME_CONFIG_KEYS)
            )
            if remaining_fields:
                f.write("\n# === CUSTOM ===\n")
                yaml.safe_dump(
                    {
                        k: config_data[k]
                        for k in config_data
                        if k not in METADATA_KEYS + RUNTIME_CONFIG_KEYS
                    },
                    f,
                    sort_keys=False,
                )

        return packaging_config

    def write_requirements(self, base_dir: Union[str, Path]):
        from packflow import __version__ as packflow_version

        base_dir = Path(base_dir).resolve()
        requirements_text = base_dir / constants.REQUIREMENTS_TEXT_NAME

        with open(requirements_text, "w") as f:
            f.write(f"packflow=={packflow_version}")

        return requirements_text


def validate_for_export(
    config: "PackflowConfig",
    project_dir: Optional[Union[str, Path]] = None,
    verbose: bool = False,
) -> tuple[list[str], list[str]]:
    """
    Validate that a PackflowConfig is ready for export.

    Returns a tuple of (errors, warnings). Errors are blocking;
    warnings are informational.
    """
    errors = []
    warnings = []

    # === METADATA FIELDS ===
    if verbose:
        click.echo("    Metadata:")

    # Validate name
    if not config.name or not config.name.strip():
        errors.append("'name' is required but is empty.")
    elif verbose:
        click.echo(f"      {click.style('✓', fg='green')} name: {config.name}")

    # Validate version
    if not config.version or not config.version.strip():
        errors.append("'version' is required for export but is empty.")
    elif verbose:
        click.echo(f"      {click.style('✓', fg='green')} version: {config.version}")

    # Validate description (warning for empty/whitespace)
    if not config.description or not config.description.strip():
        warnings.append(
            "'description' is empty. A description is recommended before distributing."
        )
    elif verbose:
        desc = (
            config.description[:50] + "..."
            if len(config.description) > 50
            else config.description
        )
        click.echo(f"      {click.style('✓', fg='green')} description: {desc}")

    # Validate maintainers (warning for empty)
    if not config.maintainers or (
        len(config.maintainers) == 1 and not config.maintainers[0].strip()
    ):
        warnings.append(
            "'maintainers' is empty. At least one maintainer is recommended before distributing."
        )
    elif verbose:
        click.echo(
            f"      {click.style('✓', fg='green')} maintainers: {', '.join(config.maintainers)}"
        )

    # === RUNTIME CONFIG FIELDS ===
    if verbose:
        click.echo("\n    Runtime:")

    # Validate inference_backend
    if verbose:
        click.echo(
            f"      {click.style('✓', fg='green')} inference_backend: {config.inference_backend}"
        )

    # Check for inference backend file (only required for local loader)
    if config.loader == "local" and project_dir:
        from pathlib import Path

        project_path = Path(project_dir).resolve()
        module_name = config.inference_backend.split(":")[0]
        backend_file = f"{module_name}.py"
        backend_path = project_path / backend_file

        if not backend_path.exists():
            errors.append(
                f"Inference backend file '{backend_file}' is missing. "
                f"Required for local loader with inference_backend '{config.inference_backend}'."
            )
            if verbose:
                click.echo(
                    f"        {click.style('✗', fg='red')} {backend_file} (missing)"
                )
        elif verbose:
            click.echo(f"        {click.style('✓', fg='green')} {backend_file}")

    if config.inference_backend == "inference:Backend":
        warnings.append(
            "'inference_backend' is set to the default template value 'inference:Backend'. "
            "Verify this is correct before distributing."
        )

    # Validate loader mode
    if verbose:
        click.echo(f"      {click.style('✓', fg='green')} loader: {config.loader}")

    # Validate Python version
    python_warning = check_python_version(config, verbose=verbose)
    if python_warning:
        warnings.append(python_warning)

    # Run loader smoke tests after all runtime fields are validated
    if config.inference_backend != "inference:Backend":
        backend_error = _validate_inference_backend(
            config, project_dir, verbose=verbose
        )
        if backend_error:
            errors.append(backend_error)

    return errors, warnings


def _validate_inference_backend(
    config: "PackflowConfig",
    project_dir: Optional[Union[str, Path]] = None,
    verbose: bool = False,
) -> Optional[str]:
    """
    Validate that the inference_backend can be loaded using proper loaders.
    Runs smoke tests for LocalLoader, ModuleLoader, and PackflowProject.from_config.
    Returns an error message if validation fails, None otherwise.
    """
    if not project_dir:
        return None

    project_dir = Path(project_dir).resolve()
    errors = []

    import os

    original_cwd = os.getcwd()

    # Show smoke tests header
    if verbose:
        click.echo("\n      Smoke tests:")

    # Test 1: Configured loader smoke test (only run the appropriate one)
    if config.loader == "local":
        if verbose:
            click.echo("        → LocalLoader.load()")
        try:
            from packflow.loaders.local import LocalLoader

            # Change to project directory for local imports
            os.chdir(project_dir)
            loader = LocalLoader(config.inference_backend)
            backend_class = loader.load_backend_module()
            if verbose:
                click.echo(
                    f"          {click.style('✓', fg='green')} LocalLoader succeeded"
                )
        except Exception as e:
            error_msg = f"LocalLoader failed: {str(e)}"
            errors.append(error_msg)
            if verbose:
                click.echo(f"          {click.style('✗', fg='red')} {error_msg}")
        finally:
            os.chdir(original_cwd)

    elif config.loader == "module":
        if verbose:
            click.echo("        → ModuleLoader.load()")
        try:
            from packflow.loaders.module import ModuleLoader

            loader = ModuleLoader(config.inference_backend)
            backend_class = loader.load_backend_module()
            if verbose:
                click.echo(
                    f"          {click.style('✓', fg='green')} ModuleLoader succeeded"
                )
        except Exception as e:
            error_msg = f"ModuleLoader failed: {str(e)}"
            errors.append(error_msg)
            if verbose:
                click.echo(f"          {click.style('✗', fg='red')} {error_msg}")

    # Test 2: InferenceBackendLoader.from_project smoke test
    if verbose:
        click.echo("        → InferenceBackendLoader.from_project()")
    try:
        from packflow.loaders.base import InferenceBackendLoader

        # Change to project directory for local imports
        os.chdir(project_dir)
        backend = InferenceBackendLoader.from_project(project_dir)
        if verbose:
            click.echo(
                f"          {click.style('✓', fg='green')} InferenceBackendLoader.from_project succeeded"
            )
    except Exception as e:
        error_msg = f"InferenceBackendLoader.from_project failed: {str(e)}"
        errors.append(error_msg)
        if verbose:
            click.echo(f"          {click.style('✗', fg='red')} {error_msg}")
    finally:
        os.chdir(original_cwd)

    # Return error if configured loader mode failed
    if config.loader == "local" and any("LocalLoader" in e for e in errors):
        return (
            f"inference_backend '{config.inference_backend}' failed LocalLoader test (configured mode): "
            + next(e for e in errors if "LocalLoader" in e)
        )
    elif config.loader == "module" and any("ModuleLoader" in e for e in errors):
        return (
            f"inference_backend '{config.inference_backend}' failed ModuleLoader test (configured mode): "
            + next(e for e in errors if "ModuleLoader" in e)
        )

    # If both tests failed, return a general error
    if len(errors) == 2:
        return f"inference_backend '{config.inference_backend}' failed all loader tests"

    return None


def check_python_version(
    config: "PackflowConfig", verbose: bool = False
) -> Optional[str]:
    """
    Compare the config's python version against the running interpreter
    at the minor version level (e.g. 3.10 vs 3.11). Returns a warning
    message string on mismatch, None if versions agree.
    """
    runtime_minor = (sys.version_info.major, sys.version_info.minor)

    try:
        parts = [int(p) for p in config.python_version.split(".")]
        config_minor = (parts[0], parts[1])
    except (ValueError, IndexError):
        return (
            f"Could not parse python_version '{config.python_version}' in packflow.yaml. "
            f"Expected a version string like '{get_python_version()}'."
        )

    if runtime_minor != config_minor:
        return (
            f"packflow.yaml specifies Python {config.python_version}, "
            f"but the current environment is Python {get_python_version()}. "
            f"Consider updating the python_version field or switching to a matching environment."
        )

    if verbose:
        click.echo(
            f"      {click.style('✓', fg='green')} python_version: {config.python_version} (matches runtime)"
        )

    return None


def _load_raw_packaging_config(base_dir: Union[str, Path]) -> dict:
    base_dir = Path(base_dir).resolve()
    packaging_config = base_dir / constants.PACKAGING_CONFIG_NAME
    try:
        with packaging_config.open("r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Not a valid packflow project: {packaging_config} does not exist"
        )


def load_packflow_config(path_or_module: str):
    """
    Check for local path FIRST -- fallback is to try to import it
    """
    project_dir = Path(path_or_module).resolve()

    if project_dir.exists():
        return PackflowConfig.from_project_path(project_dir)
    else:
        # TODO - possible to load a config from module?
        raise NotADirectoryError(
            f"Could not identify packflow project at {path_or_module}"
        )
