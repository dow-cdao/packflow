from abc import ABC, abstractmethod
import importlib
from types import ModuleType
from typing import Any, Union

from packflow.logger import get_logger


logger = get_logger()


class TypeConversionHandler(ABC):
    def __init__(self):
        self.module = self._import_module()

    def __repr__(self):  # pragma: no cover
        return self.__class__.__name__

    def _import_module(self) -> Union[ModuleType, None]:
        """
        Attempts to import the required module.

        Returns
        -------
        ModuleType
        """
        try:
            return importlib.import_module(self.package_name)
        except Exception as e:
            logger.debug(
                f"{self.__class__.__name__} Type Converter is not available. Reason: {e}"
            )
            return None

    def available(self) -> bool:
        """
        Returns if the type conversion handler is available.

        Returns
        -------
        bool
        """
        return self.module is not None

    @property
    @abstractmethod
    def package_name(self) -> str:  # pragma: no cover
        """
        The name of the required package to attempt to import
        """
        pass

    @abstractmethod
    def is_type(self, obj: Any) -> bool:  # pragma: no cover
        """
        Check if the object is the proper type for the converter

        Returns
        -------
        bool
        """
        pass

    @abstractmethod
    def convert(self, obj: Any) -> object:  # pragma: no cover
        """
        Logic to convert the type to a native, json-serializable Python type.

        Parameters
        ----------
        obj: Any
            The object to convert

        Returns
        -------
        object
            Any python native type that is JSON serializable
        """
        pass
