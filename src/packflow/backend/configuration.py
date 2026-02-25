import enum
import json
import os
from pathlib import Path
from typing import List

from deepmerge import Merger
from pydantic import BaseModel

from packflow import constants
from packflow.logger import get_logger

logger = get_logger()


class InputFormats(enum.Enum):
    """See :ref:`Preprocessors<preprocessors>` for details."""

    PASSTHROUGH = "passthrough"
    RECORDS = "records"
    NUMPY = "numpy"


class BackendConfig(BaseModel):
    """See :ref:`Backend Configuration<backend-configuration>` for details."""

    # Base configurations - controls some runtime logging behaviors
    verbose: bool = True

    # Data Requirements - controls preprocessor behavior.
    input_format: InputFormats = InputFormats.RECORDS
    rename_fields: dict = {}
    feature_names: List[str] = []
    flatten_nested_inputs: bool = False
    flatten_lists: bool = False
    nested_field_delimiter: str = "."


def load_backend_configuration(
    backend_config_model: BackendConfig | type[BackendConfig] = BackendConfig,
    **backend_kwargs,
) -> BackendConfig:
    """
    Loads, resolves, and validates base configurations and overrides.

    Parameters
    ----------
    backend_config_model : BackendConfig
        An instance of, or a subclass of, a BackendConfig Model to use for validation.
        Defaults to a base BackendConfig

    **backend_kwargs
        Optional keyword arguments to use as base parameters. These values are overridden by
        any configurations loaded from the environment configuration.

    Returns
    -------
    BackendConfig
        A validated configuration model
    """
    dict_config = _resolve_configs(backend_kwargs)

    logger.debug(f"Loaded raw configuration: {dict_config}")

    validated_config = backend_config_model.model_validate(dict_config)

    logger.info(f"Configuration: {validated_config.__repr__()}")

    return validated_config


def _load_overrides_from_env() -> dict:
    """
    Load a configuration from the file path passed via environment variable.
    This configuration overrides all in-line or default values in the provided
    BackendConfig or subclass.

    Returns
    -------
    dict

    Notes
    -----
    The configuration file must include a top level key named "configs".
    Example:
    {
      "configs": {
        "feature_names": ["foo:bar"]
      }
    }
    """
    config_file_path = os.getenv(constants.BACKEND_CONFIG_PATH_ENV_VAR_NAME)

    if not config_file_path:
        return {}

    file_path = Path(config_file_path)

    if not file_path.exists():
        logger.error(
            f"Falling back to empty configuration. Reason: Configuration file does not exist at provided path {file_path}"
        )
        return {}

    try:
        with file_path.open() as f:
            config = json.load(f)

        logger.debug(f"Loaded Overrides from environment: {config}")

        if "configs" not in config:
            logger.warning(
                'Falling back to empty configuration. Reason: Loaded config does not contain "configs" parent key.'
            )
        return config.get("configs", {})

    except Exception as e:
        logger.error(
            f"Falling back to empty configuration. Reason: Exception encountered: {e}"
        )
        return {}


def _resolve_configs(backend_kwargs: dict) -> dict:
    """
    Loads overrides from the environment and merges the configuration
    with the provided backend_kwargs.

    The Overrides will supersede any base configurations passed as
    keyword arguments or model defaults.

    Parameters
    ----------
    **backend_kwargs
        Any keyword arguments to pass to a BackendModel

    Returns
    -------
    Deep-merged configuration dictionary
    """
    merger = Merger(
        [
            (dict, "merge"),
            (list, "override"),
        ],
        ["override"],
        ["override"],
    )

    overrides = _load_overrides_from_env()

    return merger.merge(backend_kwargs, overrides)
