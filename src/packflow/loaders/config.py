import sys
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

import yaml
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

import packflow.constants as constants

METADATA_KEYS = ["name", "version", "description", "maintainers"]
RUNTIME_CONFIG_KEYS = ["inference_backend", "loader", "python_version"]


def get_python_version():
    """
    Extract semantic version of the current process' python
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def normalize_name(value: str) -> str:
    return value.replace("-", "_").strip("_")


NameStr = Annotated[
    Annotated[str, StringConstraints(pattern=r"^[A-Za-z_]+$")],
    BeforeValidator(normalize_name),
]
InferenceBackendStr = Annotated[str, StringConstraints(pattern=r"^[^:]+:[^:]+$")]


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
        return base_dir / f"{self.name}-{self.version}.zip"

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
