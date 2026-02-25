import os

import pytest
from packflow import constants
from packflow.backend import configuration

from .. import helpers


@pytest.mark.parametrize(
    "config_file_path, keyword_args, config_model, expected_result",
    [
        (None, {}, configuration.BackendConfig, configuration.BackendConfig()),
        (
            "nonexistent.json",
            {},
            configuration.BackendConfig,
            configuration.BackendConfig(),
        ),
        (
            str(helpers.get_resource_path("inference.py")),
            {},
            configuration.BackendConfig,
            configuration.BackendConfig(),
        ),
        (
            None,
            {"flatten_nested_inputs": True, "feature_names": ["bar"]},
            configuration.BackendConfig,
            configuration.BackendConfig(
                flatten_nested_inputs=True, feature_names=["bar"]
            ),
        ),
        (
            str(helpers.get_resource_path("valid-config.json")),
            {"flatten_nested_inputs": True, "feature_names": ["bar"]},
            configuration.BackendConfig,
            configuration.BackendConfig(
                flatten_nested_inputs=True,
                feature_names=["foo.bar", "baz.zip"],
                verbose=False,
            ),
        ),
    ],
)
def test_load_backend_configuration(
    config_file_path: str,
    keyword_args: dict,
    config_model: configuration.BackendConfig,
    expected_result: configuration.BackendConfig,
):
    if config_file_path:
        os.environ[constants.BACKEND_CONFIG_PATH_ENV_VAR_NAME] = config_file_path

    result = configuration.load_backend_configuration(config_model, **keyword_args)
    assert result == expected_result

    os.environ.pop(constants.BACKEND_CONFIG_PATH_ENV_VAR_NAME, None)


@pytest.mark.parametrize(
    "config_file_path, expected_result",
    [
        (None, {}),
        (str(helpers.get_resource_path("invalid-config.json")), {}),
        (
            str(helpers.get_resource_path("valid-config.json")),
            {"feature_names": ["foo.bar", "baz.zip"], "verbose": False},
        ),
    ],
)
def test__load_overrides_from_env(config_file_path: str, expected_result: dict):
    if config_file_path:
        os.environ[constants.BACKEND_CONFIG_PATH_ENV_VAR_NAME] = config_file_path

    result = configuration._load_overrides_from_env()
    assert result == expected_result

    os.environ.pop(constants.BACKEND_CONFIG_PATH_ENV_VAR_NAME, None)


@pytest.mark.parametrize(
    "config_file_path, keyword_args, expected_result",
    [
        (None, {}, {}),
        (None, {"verbose": True}, {"verbose": True}),
        (
            str(helpers.get_resource_path("invalid-config.json")),
            {"verbose": True},
            {"verbose": True},
        ),
        (
            str(helpers.get_resource_path("valid-config.json")),
            {"verbose": True},
            {"feature_names": ["foo.bar", "baz.zip"], "verbose": False},
        ),
    ],
)
def test__resolve_configs(
    config_file_path: str, keyword_args: dict, expected_result: dict
):
    if config_file_path:
        os.environ[constants.BACKEND_CONFIG_PATH_ENV_VAR_NAME] = config_file_path

    result = configuration._resolve_configs(keyword_args)
    assert result == expected_result

    os.environ.pop(constants.BACKEND_CONFIG_PATH_ENV_VAR_NAME, None)
