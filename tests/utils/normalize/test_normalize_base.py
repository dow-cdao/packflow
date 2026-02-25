from typing import Any
import sys

import numpy as np
import pytest

from packflow.utils.normalize.base import TypeConversionHandler


@pytest.mark.parametrize(
    "module_name, expected_module, expected_available_status",
    [("sys", sys, True), ("numpy", np, True), ("nonexistent", None, False)],
)
def test__import_module(module_name, expected_module, expected_available_status):
    """Test the class's ability to import modules"""

    class Handler(TypeConversionHandler):
        @property
        def package_name(self) -> str:
            return module_name

        def is_type(self, obj: Any) -> bool:
            return True

        def convert(self, obj: Any) -> object:
            return obj

    handler = Handler()

    assert handler.module is expected_module
    assert handler.available() == expected_available_status
