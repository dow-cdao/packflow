"""Stub-module tests for optional-dependency type handlers.

The tests in test_normalize_handlers.py skip when the optional package
(pandas, torch, PIL) is not installed. These tests install minimal stub
modules so the handler logic itself is always exercised, regardless of
which optional dependencies exist in the environment.
"""

import base64
import sys
from types import ModuleType

from packflow.utils.normalize.handlers import (
    PandasDataFrameHandler,
    PandasSeriesHandler,
    PillowImageHandler,
    TorchScalarHandler,
    TorchTensorHandler,
)


def _install_module(monkeypatch, name, **attrs):
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)
    return module


# -- pandas --


class _StubSeries:
    def __init__(self, data):
        self._data = data

    def to_list(self):
        return list(self._data)


class _StubDataFrame:
    def __init__(self, data):
        self._data = data

    def to_dict(self, orient):
        assert orient == "split"
        return {"index": [0], "columns": ["a"], "data": self._data}


def _install_pandas(monkeypatch):
    _install_module(monkeypatch, "pandas", Series=_StubSeries, DataFrame=_StubDataFrame)


def test_pandas_series_handler_stubbed(monkeypatch):
    """Series objects are detected and converted via to_list()"""
    _install_pandas(monkeypatch)
    handler = PandasSeriesHandler()

    series = _StubSeries([1, 2, 3])
    assert handler.is_type(series)
    assert not handler.is_type([1, 2, 3])
    assert handler.convert(series) == [1, 2, 3]


def test_pandas_dataframe_handler_stubbed(monkeypatch):
    """DataFrame objects are detected and converted via to_dict('split')"""
    _install_pandas(monkeypatch)
    handler = PandasDataFrameHandler()

    frame = _StubDataFrame([[1, 2, 3]])
    assert handler.is_type(frame)
    assert not handler.is_type({"a": 1})
    assert handler.convert(frame) == {
        "index": [0],
        "columns": ["a"],
        "data": [[1, 2, 3]],
    }


# -- torch --


class _StubTensor:
    def __init__(self, values):
        self.values = list(values)

    def numel(self):
        return len(self.values)

    def item(self):
        return self.values[0]

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        import numpy as np

        return np.array(self.values)


class _StubFloatTensor(_StubTensor):
    pass


class _StubIntTensor(_StubTensor):
    pass


def _install_torch(monkeypatch):
    _install_module(
        monkeypatch,
        "torch",
        Tensor=_StubTensor,
        FloatTensor=_StubFloatTensor,
        IntTensor=_StubIntTensor,
    )


def test_torch_scalar_handler_stubbed(monkeypatch):
    """Single-element typed tensors are detected and converted via item()"""
    _install_torch(monkeypatch)
    handler = TorchScalarHandler()

    scalar = _StubFloatTensor([5.0])
    multi = _StubIntTensor([5, 10])
    assert handler.is_type(scalar)
    assert not handler.is_type(multi)
    assert not handler.is_type(5.0)
    assert handler.convert(scalar) == 5.0


def test_torch_tensor_handler_stubbed(monkeypatch):
    """Tensors are detected and converted through detach/cpu/numpy/tolist"""
    _install_torch(monkeypatch)
    handler = TorchTensorHandler()

    tensor = _StubIntTensor([5, 10])
    assert handler.is_type(tensor)
    assert not handler.is_type([5, 10])
    assert handler.convert(tensor) == [5, 10]


# -- pillow --


class _StubImage:
    def save(self, buffer, format):
        assert format == "PNG"
        buffer.write(b"stub-image-bytes")


def test_pillow_image_handler_stubbed(monkeypatch):
    """Images are detected and converted to base64-encoded PNG bytes"""
    _install_module(monkeypatch, "PIL")
    _install_module(monkeypatch, "PIL.Image", Image=_StubImage)
    handler = PillowImageHandler()

    image = _StubImage()
    assert handler.is_type(image)
    assert not handler.is_type(b"raw bytes")

    result = handler.convert(image)
    assert base64.b64decode(result) == b"stub-image-bytes"
