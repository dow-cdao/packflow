import importlib.resources
import os
import shutil
import zipfile
from fnmatch import fnmatch
from pathlib import Path
from typing import Union

import click
import pathspec

import packflow.constants as constants

from .loaders.config import PackflowConfig, validate_for_export

# Directories excluded from export by default
EXPORT_EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    ".idea",
    ".vscode",
    ".eggs",
}

# File patterns excluded from export by default
EXPORT_EXCLUDE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.egg-info",
}

FILE_PERMISSIONS = 0o644
DIR_PERMISSIONS = 0o755


def _copy_with_perms(src: str, dst: str, **kwargs) -> str:
    """Copy file and immediately set correct permissions"""
    shutil.copy2(src, dst)
    os.chmod(dst, FILE_PERMISSIONS)
    return dst


def _copy_template_with_perms(template_src: str, dst: str):
    """Copy reference files and structure using permissions"""
    shutil.copytree(
        template_src, dst, copy_function=_copy_with_perms, dirs_exist_ok=True
    )

    # Single pass - chmod root and subdirs
    for dirpath, _dirs, _files in os.walk(dst):
        os.chmod(dirpath, DIR_PERMISSIONS)


class PackflowProject:
    def __init__(self, base_dir: Union[str, Path]):
        self.base_dir = Path(base_dir).resolve()

    @property
    def has_packflow_config(self):
        return self.base_dir.joinpath(constants.PACKAGING_CONFIG_NAME).exists()

    def __repr__(self):
        return f"{self.__class__.__name__} @ {self.base_dir}"

    @classmethod
    def create(
        cls,
        project_name: str,
        force: bool = False,
        template: str = "minimal",
        config_data: dict = None,
        optional_files: list = None,
    ):
        """
        Create a new project and then return the PackflowProject controller
        for the new project

        Parameters
        ----------
        project_name : str
            Name of the project
        force : bool
            Force initialization in existing directory
        template : str
            Template name to use
        config_data : dict, optional
            Custom configuration data for packflow.yaml fields
        optional_files : list, optional
            List of optional template files to include. If None, all files are included.
        """
        config_params = {"name": project_name}
        if config_data:
            config_params.update(config_data)
        config = PackflowConfig(**config_params)

        base_path = Path(config.name).resolve()

        created_new_dir = not base_path.exists()
        base_path.mkdir(parents=True, exist_ok=force)

        # HARD CODED SINCE THERE'S ONLY ONE TEMPLATE RIGHT NOW
        templates_dir = (
            importlib.resources.files("packflow")
            .joinpath("data/templates")
            .joinpath(template)
        )

        try:
            # Define mandatory files that must always be copied
            mandatory_files = {"inference.py", "packflow.yaml", "requirements.txt"}

            if optional_files is None:
                # Copy all template files
                _copy_template_with_perms(str(templates_dir), str(base_path))
            else:
                # Selectively copy files
                files_to_copy = mandatory_files | set(optional_files)

                for file_name in files_to_copy:
                    src_file = templates_dir / file_name
                    if src_file.exists():
                        dst_file = base_path / file_name
                        shutil.copy2(str(src_file), str(dst_file))
                        os.chmod(dst_file, FILE_PERMISSIONS)

            config.write_yaml(base_path)

            config.write_requirements(base_path)
        except Exception:
            if created_new_dir:
                shutil.rmtree(base_path, ignore_errors=True)
            raise

        return cls(base_path)

    def load_config(self):
        return PackflowConfig.from_project_path(self.base_dir)

    # Files that must always be present for a valid export
    REQUIRED_FILES = [
        constants.PACKAGING_CONFIG_NAME,  # packflow.yaml
        constants.REQUIREMENTS_TEXT_NAME,  # requirements.txt
    ]

    # Files that are recommended but not required
    RECOMMENDED_FILES = [
        "MODEL_CARD.md",
        "LICENSE.txt",
        "README.md",
    ]

    def validate_required_files(
        self, verbose: bool = False, config: PackflowConfig = None
    ) -> tuple[list[str], list[str]]:
        """
        Check that required and recommended project files are present and valid.

        For local loader mode, validates that the inference backend file exists
        based on the inference_backend configuration (e.g., inference:Backend
        requires inference.py, custom_module:Backend requires custom_module.py).

        Returns a tuple of (errors, warnings).
        """
        errors = []
        warnings = []

        # Check required files
        if verbose:
            click.echo("\nRequired files:")

        for filename in self.REQUIRED_FILES:
            file_path = self.base_dir / filename
            if not file_path.exists():
                errors.append(f"Required file '{filename}' is missing.")
                if verbose:
                    click.echo(f"  {click.style('✗', fg='red')} {filename} (missing)")
            else:
                # Special validation for packflow.yaml - show fields as sub-items
                if filename == constants.PACKAGING_CONFIG_NAME:
                    if verbose:
                        click.echo(f"  {click.style('✓', fg='green')} {filename}")
                    # Validate config fields as sub-items
                    if config:
                        config_errors, config_warnings = validate_for_export(
                            config, project_dir=self.base_dir, verbose=verbose
                        )
                        errors.extend(config_errors)
                        warnings.extend(config_warnings)
                # Special validation for requirements.txt
                elif filename == constants.REQUIREMENTS_TEXT_NAME:
                    if verbose:
                        click.echo(f"  {click.style('✓', fg='green')} {filename}")

                    req_content = file_path.read_text()
                    if "packflow" not in req_content.lower():
                        errors.append("'packflow' is not listed in requirements.txt.")
                        if verbose:
                            click.echo(
                                f"    {click.style('✗', fg='red')} missing 'packflow' dependency"
                            )
                    else:
                        # Check for version mismatches and missing packages (shows as sub-items)
                        req_warnings = self._validate_requirements(file_path, verbose)
                        warnings.extend(req_warnings)
                else:
                    if verbose:
                        click.echo(f"  {click.style('✓', fg='green')} {filename}")

        # Check recommended files
        if verbose:
            click.echo("\nRecommended files:")

        for filename in self.RECOMMENDED_FILES:
            file_path = self.base_dir / filename
            if not file_path.exists():
                warnings.append(f"Recommended file '{filename}' is missing.")
                if verbose:
                    click.echo(
                        f"  {click.style('⚠', fg='yellow')} {filename} (missing)"
                    )
            else:
                # Check if file is empty or still template content
                content = file_path.read_text().strip()
                status = None

                if not content:
                    status = "empty"
                    warnings.append(f"'{filename}' is empty.")
                elif filename == "MODEL_CARD.md":
                    # Check for template placeholders
                    if "{introduction}" in content:
                        status = "template"
                        warnings.append(
                            f"'{filename}' appears to be unchanged from template."
                        )
                elif filename == "README.md":
                    # Check for template content
                    if (
                        "# Project Name" in content
                        or "Brief description of the analytic" in content
                    ):
                        status = "template"
                        warnings.append(
                            f"'{filename}' appears to be unchanged from template."
                        )

                if verbose:
                    if status:
                        click.echo(
                            f"  {click.style('⚠', fg='yellow')} {filename} ({status})"
                        )
                    else:
                        click.echo(f"  {click.style('✓', fg='green')} {filename}")

        return errors, warnings

    def _validate_requirements(
        self, requirements_file: Path, verbose: bool = False
    ) -> list[str]:
        """
        Validate requirements.txt against the current environment.
        Returns a list of warnings.
        """
        import re
        from importlib.metadata import PackageNotFoundError, version

        from packaging.requirements import Requirement
        from packaging.specifiers import SpecifierSet

        from packflow import __version__ as current_packflow_version

        warnings = []
        req_content = requirements_file.read_text()

        # Parse requirements
        for line in req_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse package name and version specifier
            match = re.match(r"^([a-zA-Z0-9_-]+)([=<>!]+.*)?$", line)
            if not match:
                continue

            package_name = match.group(1)
            version_spec = match.group(2) or ""

            # Special handling for packflow version check
            if package_name.lower() == "packflow":
                if version_spec:
                    # Extract version from spec (e.g., "==1.0.0" -> "1.0.0")
                    version_match = re.search(r"[\d.]+", version_spec)
                    if version_match:
                        req_version = version_match.group(0)
                        if req_version != current_packflow_version:
                            warning = (
                                f"requirements.txt specifies packflow{version_spec}, "
                                f"but installed version is {current_packflow_version}."
                            )
                            warnings.append(warning)
                            if verbose:
                                click.echo(
                                    f"    {click.style('⚠', fg='yellow')} packflow version mismatch "
                                    f"(installed: {current_packflow_version}, required: {req_version})"
                                )
                        elif verbose:
                            click.echo(
                                f"    {click.style('✓', fg='green')} {package_name}"
                            )
                    elif verbose:
                        click.echo(f"    {click.style('✓', fg='green')} {package_name}")
                continue

            # Check if package is installed
            try:
                installed_version = version(package_name)

                # Check version compatibility if specified
                if version_spec:
                    try:
                        req = Requirement(line)
                        if req.specifier and installed_version not in req.specifier:
                            warning = (
                                f"Package '{package_name}' version {installed_version} "
                                f"does not match requirement '{line}'."
                            )
                            warnings.append(warning)
                            if verbose:
                                click.echo(
                                    f"    {click.style('⚠', fg='yellow')} {package_name} version mismatch"
                                )
                        elif verbose:
                            click.echo(
                                f"    {click.style('✓', fg='green')} {package_name}"
                            )
                    except Exception:
                        # If we can't parse the requirement, just show it's installed
                        if verbose:
                            click.echo(
                                f"    {click.style('✓', fg='green')} {package_name}"
                            )
                elif verbose:
                    # No version spec, just show it's installed
                    click.echo(f"    {click.style('✓', fg='green')} {package_name}")
            except PackageNotFoundError:
                warning = f"Package '{package_name}' from requirements.txt is not installed in the current environment."
                warnings.append(warning)
                if verbose:
                    click.echo(
                        f"    {click.style('⚠', fg='yellow')} {package_name} not installed"
                    )

        return warnings

    def _load_gitignore_spec(self) -> pathspec.PathSpec:
        """Load .gitignore patterns if the file exists."""
        gitignore = self.base_dir / ".gitignore"
        if not gitignore.exists():
            return pathspec.PathSpec.from_lines("gitwildmatch", [])
        return pathspec.PathSpec.from_lines(
            "gitwildmatch", gitignore.read_text().splitlines()
        )

    def export(self, output_directory: str = ".", verbose: bool = False) -> Path:
        """
        Save the loaded project as a package.zip with schema `{name}-{version}.zip`
        """
        if verbose:
            click.echo("\n=== Export Validation ===")
            click.echo(f"Project: {self.base_dir}")

        config = PackflowConfig.from_project_path(self.base_dir)

        # Validate files (packflow.yaml validation will be integrated)
        file_errors, file_warnings = self.validate_required_files(
            verbose=verbose, config=config
        )
        errors = file_errors
        warnings = file_warnings

        if errors:
            raise ValueError(
                "Export blocked due to validation errors:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

        self.export_warnings = warnings

        export_file_name = config.archive_file_name(output_directory)

        try:
            with zipfile.ZipFile(export_file_name, "w") as zip_file:
                for file_path in self.base_dir.rglob("*"):
                    if not file_path.is_file():
                        continue
                    if file_path.resolve() == export_file_name.resolve():
                        continue

                    relative_path = file_path.relative_to(self.base_dir)

                    # Skip files inside excluded directories
                    if any(part in EXPORT_EXCLUDE_DIRS for part in relative_path.parts):
                        continue

                    # Skip files matching excluded patterns
                    if any(
                        fnmatch(file_path.name, pat) for pat in EXPORT_EXCLUDE_PATTERNS
                    ):
                        continue

                    zip_file.write(str(file_path), str(relative_path))
            return export_file_name
        except Exception as e:
            # TODO: Create custom exception
            raise Exception(f"An error occurred: {e}")
