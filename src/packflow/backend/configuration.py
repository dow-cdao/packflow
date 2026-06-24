import enum
from typing import List

from pydantic import BaseModel

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
    verbose: bool = False

    # Data Requirements - controls preprocessor behavior.
    input_format: InputFormats = InputFormats.RECORDS
    rename_fields: dict = {}
    feature_names: List[str] = []
    flatten_nested_inputs: bool = False
    flatten_lists: bool = False
    nested_field_delimiter: str = "."
    ignore_delimiter_collisions: bool = False

    # Output metadata - declarative only; checked by backend.check_io()
    output_keys: List[str] = []


def load_backend_configuration(
    backend_config_model: BackendConfig | type[BackendConfig] = BackendConfig,
    **backend_kwargs,
) -> BackendConfig:
    """
    Loads and validates backend configuration.

    Parameters
    ----------
    backend_config_model : BackendConfig
        An instance of, or a subclass of, a BackendConfig Model to use for validation.
        Defaults to a base BackendConfig

    **backend_kwargs
        Keyword arguments used as configuration values. When loading from a packflow
        project, these are populated from the ``backend_config`` section of
        ``packflow.yaml``, with any caller-supplied overrides merged on top.

    Returns
    -------
    BackendConfig
        A validated configuration model
    """
    logger.debug(f"Loaded raw configuration: {backend_kwargs}")

    validated_config = backend_config_model.model_validate(backend_kwargs)

    logger.info(f"Configuration: {validated_config.__repr__()}")

    return validated_config
