from packflow.backend import configuration


def test_load_backend_configuration_defaults():
    result = configuration.load_backend_configuration(configuration.BackendConfig)
    assert result == configuration.BackendConfig()


def test_load_backend_configuration_with_kwargs():
    result = configuration.load_backend_configuration(
        configuration.BackendConfig,
        flatten_nested_inputs=True,
        feature_names=["bar"],
    )
    assert result == configuration.BackendConfig(
        flatten_nested_inputs=True, feature_names=["bar"]
    )


def test_load_backend_configuration_custom_model():
    from pydantic import BaseModel
    from packflow.backend.configuration import BackendConfig

    class CustomConfig(BackendConfig):
        threshold: float = 0.5

    result = configuration.load_backend_configuration(CustomConfig, threshold=0.9)
    assert result.threshold == 0.9
    assert result == CustomConfig(threshold=0.9)


def test_load_backend_configuration_from_packflow_yaml_dict():
    """Simulates values arriving from packflow.yaml backend_config section."""
    yaml_backend_config = {"feature_names": ["foo.bar", "baz.zip"], "verbose": False}

    result = configuration.load_backend_configuration(
        configuration.BackendConfig, **yaml_backend_config
    )
    assert result == configuration.BackendConfig(
        feature_names=["foo.bar", "baz.zip"], verbose=False
    )


def test_load_backend_configuration_kwargs_override_yaml():
    """Explicit kwargs take priority over packflow.yaml values (merged upstream)."""
    yaml_backend_config = {"feature_names": ["from_yaml"], "verbose": True}
    explicit_kwargs = {"verbose": False}

    merged = {**yaml_backend_config, **explicit_kwargs}
    result = configuration.load_backend_configuration(
        configuration.BackendConfig, **merged
    )
    assert result.verbose is False
    assert result.feature_names == ["from_yaml"]
