import base64
import io
from typing import Any

from .base import TypeConversionHandler

# -- NUMPY --


class NumpyTypeHandler(TypeConversionHandler):
    @property
    def package_name(self) -> str:
        return "numpy"

    def is_type(self, obj: Any) -> bool:
        return isinstance(obj, (self.module.ndarray, self.module.generic))

    def convert(self, obj: Any) -> object:
        return obj.tolist()


# -- PANDAS --


class PandasSeriesHandler(TypeConversionHandler):
    @property
    def package_name(self) -> str:
        return "pandas"

    def is_type(self, obj: Any) -> bool:
        return isinstance(obj, self.module.Series)

    def convert(self, obj: Any) -> object:
        return obj.to_list()


class PandasDataFrameHandler(TypeConversionHandler):
    @property
    def package_name(self) -> str:
        return "pandas"

    def is_type(self, obj: Any) -> bool:
        return isinstance(obj, self.module.DataFrame)

    def convert(self, obj: Any) -> object:
        return obj.to_dict("split")


# -- TORCH --


class TorchScalarHandler(TypeConversionHandler):
    @property
    def package_name(self) -> str:
        return "torch"

    def is_type(self, obj: Any) -> bool:
        return (
            isinstance(obj, (self.module.FloatTensor, self.module.IntTensor))
            and obj.numel() == 1
        )

    def convert(self, obj: Any) -> object:
        return obj.item()


class TorchTensorHandler(TypeConversionHandler):
    @property
    def package_name(self) -> str:
        return "torch"

    def is_type(self, obj: Any) -> bool:
        return isinstance(obj, self.module.Tensor)

    def convert(self, obj: Any) -> object:
        return obj.detach().cpu().numpy().tolist()


# -- PILLOW/PIL --


class PillowImageHandler(TypeConversionHandler):
    @property
    def package_name(self) -> str:
        return "PIL.Image"

    def is_type(self, obj: Any) -> bool:
        return isinstance(obj, self.module.Image)

    def convert(self, obj: Any) -> object:
        buffer = io.BytesIO()
        obj.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
