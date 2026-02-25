from typing import Any, Dict, Iterable

from .handlers import (
    NumpyTypeHandler,
    PandasSeriesHandler,
    PandasDataFrameHandler,
    TorchScalarHandler,
    TorchTensorHandler,
    PillowImageHandler,
)

# Prioritized list (most likely to be encountered first) of TypeConversionHandlers
_ALL_HANDLERS = [
    NumpyTypeHandler(),
    PandasSeriesHandler(),
    PandasDataFrameHandler(),
    TorchScalarHandler(),
    TorchTensorHandler(),
    PillowImageHandler(),
]

# Filtered list of which handlers are available in the current environment
_AVAILABLE_HANDLERS = [handler for handler in _ALL_HANDLERS if handler.available()]


def ensure_native_types(obj: Any):
    """Converts any non-native data types to ensure JSON serialization is possible.

    Parameters
    ----------
    obj  : Any
        the object to convert to a native data type

    Returns
    -------
    A scalar or object with all-native Python data types
    """
    # Bypass handlers if the obj is already a native scalar type
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj

    # If not, loop through available handlers and convert to an allowed type
    for handler in _AVAILABLE_HANDLERS:
        if handler.is_type(obj):
            return handler.convert(obj)

    # Handle containers
    if isinstance(obj, dict):
        return {k: ensure_native_types(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [ensure_native_types(v) for v in obj]

    # Throw an error if there's an unknown type
    raise TypeError(
        f'Returned type "{type(obj)}" is not supported. Please convert this object to a native Python type in your app.'
    )


def ensure_valid_output(
    output: Iterable[Any], parent_key: str = "output"
) -> Iterable[Dict[str, Any]]:
    """
    Coerces outputs to native Python types and correct formats.

    Parameters
    ----------
    output : Iterable[Any]
        Model outputs to be cleaned

    parent_key : str
        Default 'output'. Used when the output is not a dictionary type.
        Ex: Output of [0, 1] would be wrapped to {f'{parent_key}': [0, 1]}

    Returns
    -------
    List[Dict[str, Any]]
    """
    valid_output = []
    for v in output:
        v = ensure_native_types(v)
        if not isinstance(v, dict):
            if isinstance(v, list) and len(v) == 1:
                v = v[0]
            v = {parent_key: v}
        valid_output.append(v)
    return valid_output
