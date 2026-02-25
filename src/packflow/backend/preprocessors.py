from abc import ABC, abstractmethod

import numpy as np
from flatten_dict import flatten, unflatten
from flatten_dict.reducers import make_reducer
from flatten_dict.splitters import make_splitter
from loguru import logger

import packflow.exceptions as exceptions
import packflow.utils

from .configuration import BackendConfig, InputFormats


def get_preprocessor(config: BackendConfig):
    """
    Instantiate a preprocessor based on the provided BackendConfig.

    Parameters
    ----------
    config : BackendConfig
        The packflow BackendConfig for the inference backend.

    Returns
    -------
    Preprocessor

    Raises
    ------
    UnknownPreprocessorError

    Notes
    -----
    This is a general factory function for simpler loading of preprocessor objects.
    All subclasses of the Preprocessor object follow the same API and be executed
    generically.
    """
    if config.input_format == InputFormats.RECORDS:
        preprocessor = RecordsPreprocessor(config)
    elif config.input_format == InputFormats.NUMPY:
        preprocessor = NumpyPreprocessor(config)
    else:
        preprocessor = PassthroughPreprocessor(config)

    return preprocessor


class Preprocessor(ABC):
    """Base class for Packflow preprocessors"""

    def __init__(self, config: BackendConfig):
        self.config = config
        self.resolve()

    def __repr__(self):  # pragma: no cover
        return f"{self.__class__.__name__}[\n  {self.config.__repr__()}\n]"

    def __call__(self, raw_inputs: list[dict]):
        """
        Run the preprocessor against raw inputs and return the processed data
        """
        try:
            return self.process(raw_inputs)
        except Exception as e:
            raise exceptions.PreprocessorRuntimeError(
                f"Failed to preprocess inputs with the following exception: {e}"
            ) from e

    @abstractmethod
    def resolve(self):  # pragma: no cover
        """
        Check the config for required fields or conditions that may not
        be caught by the pydantic model.
        """
        pass

    @abstractmethod
    def process(self, raw_inputs: list[dict]):  # pragma: no cover
        """
        Run the preprocessor against raw inputs and return the processed data
        """
        pass


class PassthroughPreprocessor(Preprocessor):
    """Passthrough preprocessor that does nothing."""

    def resolve(self):
        """Ignored, as all data is passed through."""
        return

    def process(self, raw_inputs: list[dict]) -> list[dict]:
        """Return inputs without any preprocessing."""
        return raw_inputs


class RecordsPreprocessor(Preprocessor):
    """
    Records preprocessor that is highly optimized for:
      - filtering fields
      - ensuring proper order of keys
      - flattening nested fields/lists
    """

    def resolve(self):
        """
        Resolve the config to ensure that required fields are satisfied.

        Returns
        -------
        None

        Notes
        -----
        This preprocessor may default to being a passthrough if a specific subset of
        config fields are not set. For example, if the config specifies that there are
        no fields to rename, no filtering to be done, or flattening is not enabled, then
        the run() method will default to passing through data for performance.
        """
        self.passthrough = not any(
            (
                self.config.rename_fields,
                self.config.feature_names,
                self.config.flatten_nested_inputs,
            )
        )

        if self.passthrough:
            logger.info(
                "Current config does not require preprocessing steps. Defaulting to Passthrough mode."
            )
            return

        self.reducer = make_reducer(self.config.nested_field_delimiter)
        self.enumerate_types = (list,) if self.config.flatten_lists else ()

    def process(self, raw_inputs: list[dict]) -> list[dict]:
        """Process an input batch and make transformations as necessary.

        This preprocessor focuses on three main transformations:
            1. Renaming input fields
            2. Filtering to only required fields
            3. Flattening objects (dictionaries and/or lists)

        Parameters
        ----------
        raw_inputs : list[dict]
            Raw input records to transform

        Returns
        -------
        list[dict]
            Transformed records
        """
        if self.passthrough:
            return raw_inputs

        records = []
        for obj in raw_inputs:
            obj = obj.copy()  # avoid editing input data
            obj = flatten(
                obj,
                reducer=self.reducer,
                enumerate_types=self.enumerate_types,
                keep_empty_types=(dict, list),
            )
            processed_obj = {}

            for key in self.config.rename_fields:
                processed_obj[self.config.rename_fields[key]] = obj.get(key)

            if self.config.feature_names:
                for feature in self.config.feature_names:
                    if feature not in processed_obj:
                        processed_obj[feature] = obj.get(feature)
            else:
                processed_obj.update(obj)

            if not self.config.flatten_nested_inputs:
                processed_obj = unflatten(
                    processed_obj,
                    splitter=make_splitter(self.config.nested_field_delimiter),
                )

            records.append(processed_obj)

        return records


class NumpyPreprocessor(Preprocessor):
    """
    Converts input records to a numpy array.
    """

    def resolve(self):
        """
        Check the config for required fields.

        Returns
        -------
        None

        Notes
        -----
        This preprocessor will only execute if the user has specified `feature_names`.
        """
        if not self.config.feature_names:
            raise exceptions.PreprocessorInitError(
                f"This preprocessor requires `feature_names` to be defined. Received config: {self.config.__repr__()}"
            )

        reverse_rename = {v: k for k, v in self.config.rename_fields.items()}

        self.features = [
            reverse_rename.get(feature, feature)
            for feature in self.config.feature_names
        ]

    def process(self, raw_inputs: list[dict]) -> np.array:
        """
        Convert the records to a numpy array.

        Parameters
        ----------
        raw_inputs: list[dict]

        Returns
        -------
        array

        """
        return packflow.utils.records_to_ndarray(
            raw_inputs,
            feature_names=self.features,
            dtype=None,
            delimiter=self.config.nested_field_delimiter,
        )
