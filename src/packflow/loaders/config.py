import sys
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

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


def validate_for_export(config: "PackflowConfig") -> tuple[list[str], list[str]]:
    """
    Validate that a PackflowConfig is ready for export.

    Returns a tuple of (errors, warnings). Errors are blocking;
    warnings are informational.
    """
    errors = []
    warnings = []

    if not config.version:
        errors.append("'version' is required for export but is empty.")

    if config.inference_backend == "inference:Backend":
        warnings.append(
            "'inference_backend' is set to the default template value 'inference:Backend'. "
            "Verify this is correct before distributing."
        )

    if not config.description:
        warnings.append(
            "'description' is empty. A description is recommended before distributing."
        )

    if not config.maintainers:
        warnings.append(
            "'maintainers' is empty. At least one maintainer is recommended before distributing."
        )

    return errors, warnings


def check_python_version(config: "PackflowConfig") -> Optional[str]:
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
