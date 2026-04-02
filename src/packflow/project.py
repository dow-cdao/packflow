import importlib.resources
import os
import shutil
import zipfile
from fnmatch import fnmatch
from pathlib import Path
from typing import Union

import pathspec

import packflow.constants as constants

from .loaders.config import PackflowConfig, check_python_version

# Directories excluded from export by default
EXCLUDED_DIRS = {
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


class PackflowProject:
    def __init__(self, base_dir: Union[str, Path]):
        self.base_dir = Path(base_dir).resolve()

    @property
    def has_packflow_config(self):
        return self.base_dir.joinpath(constants.PACKAGING_CONFIG_NAME).exists()

    def __repr__(self):
        return f"{self.__class__.__name__} @ {self.base_dir}"

    @classmethod
    def create(cls, project_name: str, force: bool = False, template: str = "minimal"):
        """
        Create a new project and then return the PackflowProject controller
        for the new project
        """
        config = PackflowConfig(name=project_name)

        base_path = Path(config.name).resolve()

        created_new_dir = not base_path.exists()
        base_path.mkdir(parents=True, exist_ok=force)

        # HARD CODED SINCE THERE'S ONLY ONE TEMPLATE RIGHT NOW
        templates_dir = (
            importlib.resources.files("packflow")
            .joinpath("data/templates")
            .joinpath(template)
        )

        shutil.copytree(str(templates_dir), str(base_path), dirs_exist_ok=True)

        try:
            # Ensure all created files/directories are writable regardless of
            # source permissions or environment umask settings
            os.chmod(base_path, 0o755)
            for root, dirs, files in os.walk(base_path):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o644)

            config.write_yaml(base_path)

            config.write_requirements(base_path)
        except Exception:
            if created_new_dir:
                shutil.rmtree(base_path, ignore_errors=True)
            raise

        return cls(base_path)

    def load_config(self):
        return PackflowConfig.from_project_path(self.base_dir)

    def _load_gitignore_spec(self) -> pathspec.PathSpec:
        """Load .gitignore patterns if the file exists."""
        gitignore = self.base_dir / ".gitignore"
        if not gitignore.exists():
            return pathspec.PathSpec.from_lines("gitwildmatch", [])
        return pathspec.PathSpec.from_lines(
            "gitwildmatch", gitignore.read_text().splitlines()
        )


    def export(self, output_directory: str = ".") -> Path:
        """
        Save the loaded project as a package.zip with schema `{name}-{version}.zip`
        """
        config = PackflowConfig.from_project_path(self.base_dir)

        self.version_warning = check_python_version(config)

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
