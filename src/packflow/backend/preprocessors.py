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

    def _check_for_delimiter_collisions(self, obj: dict) -> None:
        """Check if any keys in the object contain the delimiter character.
        
        Raises PreprocessorRuntimeError if collisions are found and
        ignore_delimiter_collisions is False.
        
        Parameters
        ----------
        obj : dict
            Dictionary to check for delimiter collisions
        """
        if self.config.ignore_delimiter_collisions:
            return
        
        collisions = packflow.utils.check_delimiter_collisions(
            obj, self.config.nested_field_delimiter
        )
        
        if collisions:
            raise exceptions.PreprocessorRuntimeError(
                f"Keys containing the delimiter '{self.config.nested_field_delimiter}' were found: {collisions}. "
                f"This can cause ambiguity when using nested path access. "
                f"Either rename these keys or set ignore_delimiter_collisions=True to bypass this check. "
                f"Note: Setting ignore_delimiter_collisions=True may result in undefined behavior "
                f"if key collisions occur during flatten/unflatten operations."
            )
    
    def _uses_nested_paths(self) -> bool:
        """Check if any rename_fields keys or feature_names use nested path notation.
        
        Returns True if delimiter is present in any field names.
        """
        delimiter = self.config.nested_field_delimiter
        
        for key in self.config.rename_fields:
            if delimiter in key:
                return True
        
        for feature in self.config.feature_names:
            if delimiter in feature:
                return True
        
        return False

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

        Notes
        -----
        When accessing nested fields via delimiter notation (e.g., "a.b.c") in
        feature_names or rename_fields, missing keys will be silently skipped
        and not included in the output.
        
        If flatten_nested_inputs=False, the preprocessor will never flatten the input,
        preserving all keys exactly as they appear (including keys containing delimiters).
        Nested path access will be done via direct traversal instead of flattening.
        """
        if self.passthrough:
            return raw_inputs

        uses_nested_paths = self._uses_nested_paths()
        
        # Check for delimiter collisions if we're using nested paths
        if uses_nested_paths and not self.config.flatten_nested_inputs:
            for obj in raw_inputs:
                self._check_for_delimiter_collisions(obj)

        records = []
        for obj in raw_inputs:
            obj = obj.copy()  # avoid editing input data
            
            if self.config.flatten_nested_inputs:
                # FLATTEN MODE: Flatten the entire structure
                obj = flatten(
                    obj,
                    reducer=self.reducer,
                    enumerate_types=self.enumerate_types,
                    keep_empty_types=(dict, list),
                )
                processed_obj = {}
                
                # Process rename_fields with flattened keys
                for key in self.config.rename_fields:
                    value = obj.get(key)
                    if value is not None:
                        processed_obj[self.config.rename_fields[key]] = value
                
                # Process feature_names with flattened keys
                if self.config.feature_names:
                    for feature in self.config.feature_names:
                        if feature not in processed_obj:
                            value = obj.get(feature)
                            if value is not None:
                                processed_obj[feature] = value
                else:
                    processed_obj.update(obj)
            else:
                # NON-FLATTEN MODE: Preserve structure, use direct nested access
                processed_obj = {}
                
                # Process rename_fields with direct nested access
                for key in self.config.rename_fields:
                    value = packflow.utils.get_nested_field_direct(
                        obj, key, self.config.nested_field_delimiter
                    )
                    if value is not None:
                        new_key = self.config.rename_fields[key]
                        # If the new key contains delimiter, create nested structure
                        if self.config.nested_field_delimiter in new_key:
                            packflow.utils.set_nested_field_direct(
                                processed_obj, new_key, value, self.config.nested_field_delimiter
                            )
                        else:
                            processed_obj[new_key] = value
                
                # Process feature_names with direct nested access
                if self.config.feature_names:
                    for feature in self.config.feature_names:
                        # Check if already added via rename_fields
                        existing_value = packflow.utils.get_nested_field_direct(
                            processed_obj, feature, self.config.nested_field_delimiter
                        )
                        if existing_value is None:
                            value = packflow.utils.get_nested_field_direct(
                                obj, feature, self.config.nested_field_delimiter
                            )
                            if value is not None:
                                # If feature contains delimiter, create nested structure
                                if self.config.nested_field_delimiter in feature:
                                    packflow.utils.set_nested_field_direct(
                                        processed_obj, feature, value, self.config.nested_field_delimiter
                                    )
                                else:
                                    processed_obj[feature] = value
                else:
                    # No feature filtering - include everything
                    processed_obj.update(obj)

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
