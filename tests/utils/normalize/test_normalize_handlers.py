from importlib.util import find_spec
import json

import numpy as np
import pytest

from packflow.utils.normalize.handlers import (
    NumpyTypeHandler,
    PandasSeriesHandler,
    PandasDataFrameHandler,
    TorchScalarHandler,
    TorchTensorHandler,
    PillowImageHandler,
)

from ... import helpers


@pytest.mark.parametrize(
    "value, expected_result",
    [
        (np.int16(5), 5),
        (np.array([1, 2, 3], dtype=np.int16), [1, 2, 3]),
        (np.array([1.0, 2.0, 3.0], dtype=np.float32), [1.0, 2.0, 3.0]),
        (np.array([[1.0, 2.0, 3.0]], dtype=np.float32), [[1.0, 2.0, 3.0]]),
        (5, None),
    ],
)
def test_numpy_type_handler(value, expected_result):
    handler = NumpyTypeHandler()

    if handler.is_type(value):
        result = handler.convert(value)
    else:
        result = None

    assert result == expected_result

    if result:
        assert json.dumps(result)


@pytest.mark.skipif(not find_spec("pandas"), reason="Pandas is not installed")
@pytest.mark.parametrize(
    "series_kwargs, expected_result",
    [
        ({"data": [1, 2, 3], "dtype": "int16"}, [1, 2, 3]),
        ({"data": [1.0, 2.0, 3.0], "dtype": "float32"}, [1.0, 2.0, 3.0]),
        ({"data": [], "dtype": "float32"}, []),
    ],
)
def test_pandas_series_handler(series_kwargs, expected_result):
    from pandas import Series

    handler = PandasSeriesHandler()

    data = Series(**series_kwargs)

    assert handler.is_type(data)

    result = handler.convert(data)
    assert result == expected_result
    assert json.dumps(result)


@pytest.mark.skipif(not find_spec("pandas"), reason="Pandas is not installed")
@pytest.mark.parametrize(
    "df_kwargs, expected_result",
    [
        (
            {"data": [[1, 2, 3]], "columns": ["one", "two", "three"], "dtype": "int16"},
            {"index": [0], "columns": ["one", "two", "three"], "data": [[1, 2, 3]]},
        ),
        ({}, {"index": [], "columns": [], "data": []}),
    ],
)
def test_pandas_dataframe_handler(df_kwargs, expected_result):
    from pandas import DataFrame

    handler = PandasDataFrameHandler()
    data = DataFrame(**df_kwargs)
    assert handler.is_type(data)

    result = handler.convert(data)
    assert result == expected_result
    assert json.dumps(result)


@pytest.mark.skipif(not find_spec("torch"), reason="Torch is not installed")
@pytest.mark.parametrize(
    "cls_name, value, expected_result",
    [
        ("IntTensor", [5], 5),
        ("FloatTensor", [5.0], 5.0),
        ("IntTensor", [5, 10], [5, 10]),
        ("FloatTensor", [5.0, 10.0], [5.0, 10.0]),
    ],
)
def test_torch_handlers(cls_name, value, expected_result):
    import torch

    obj = getattr(torch, cls_name)(value)

    scalar_handler = TorchScalarHandler()
    tensor_handler = TorchTensorHandler()

    if scalar_handler.is_type(obj):
        result = scalar_handler.convert(obj)
    elif tensor_handler.is_type(obj):
        result = tensor_handler.convert(obj)
    else:
        result = None

    assert result == expected_result
    assert json.dumps(result)


@pytest.mark.skipif(not find_spec("PIL"), reason="pillow (PIL) is not installed")
def test_pillow_image_handler():
    from PIL import Image

    image_path = str(helpers.get_resource_path("test_image.jpeg"))

    im = Image.open(image_path)

    handler = PillowImageHandler()

    assert handler.is_type(im)
    result = handler.convert(im)
    assert json.dumps(result)
