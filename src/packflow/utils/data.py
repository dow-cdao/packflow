import functools
from typing import Any, List, Optional

import numpy as np
from flatten_dict import flatten, unflatten
from flatten_dict.reducers import make_reducer


def get_nested_field(obj: dict, field: str, delimiter: Optional[str] = None) -> Any:
    """
    Retrieves a single nested field from a dictionary given a field name.

    Example: get_nested_field({"foo": {"bar": 5}}, 'foo.bar') -> 5

    Parameters
    ----------
    obj : dict
        An arbitrary dictionary of data

    field : str
        The key name to retrieve where subfields are split by $delimiter

    Returns
    -------
    Any
        The value retrieved from the nested key
    """
    if field in obj:
        return obj[field]

    flattened = flatten(
        obj, reducer=make_reducer(delimiter or "."), keep_empty_types=(dict, list)
    )
    return flattened.get(field, None)


def records_to_ndarray(
    records: List[dict],
    feature_names: List[str],
    dtype: Optional[str] = None,
    delimiter: Optional[str] = None,
) -> np.ndarray:
    """
    Converts records to a numpy nd array

    Example
    -------
    in: [{"num": 1, "num2": 1}, {"num": 2, "num": 2}]
    args: feature_names=["num", "num2"]
    out: np.array([[1, 1], [2, 2]])

    Parameters
    ----------
    records : List[Dict]
        A list of dictionary items to be converted

    feature_names : List[str]
        The values to extract for each row

    dtype : str
        The numpy data type to coerce the array to. Defaults to 'float32'

    Returns
    -------
    numpy.ndarray
    """
    if not isinstance(records, list):
        raise ValueError(
            f"Value for `records` must be a list of dictionaries. Received type: {type(records)}"
        )

    # Pre-allocate list with None values for better performance
    arr_data = [[None] * len(feature_names) for _ in range(len(records))]

    for index, row in enumerate(records):
        if not isinstance(row, dict):
            raise ValueError(
                f"Value at index {index} is not a dictionary. Received type: {type(row)}"
            )

        # Use list comprehension with direct assignment
        arr_data[index] = [
            get_nested_field(row, feature, delimiter=delimiter)
            for feature in feature_names
        ]

    return np.array(arr_data, dtype=dtype)


def flatten_dict(obj: dict, delimiter: str = ".", flatten_lists: bool = False) -> dict:
    """
    Create a flattened dictionary from a nested object.

    Parameters
    ----------
    obj: dict

    delimiter: str
        Default '.'

    flatten_lists: bool
        Default False

    Returns
    -------
    dict
        Flattened dictionary.
    """
    if not isinstance(obj, dict):
        raise TypeError(
            f"Value for `obj` must be a dictionary-like object. Received type: {type(obj)}"
        )

    return flatten(
        obj,
        reducer=make_reducer(delimiter),
        enumerate_types=(list,) if flatten_lists else (),
        keep_empty_types=(dict, list),
    )


def flatten_records(
    records: List[dict], delimiter: str = ".", flatten_lists: bool = False
) -> List[dict]:
    """
    Flatten a list of dictionaries

    Parameters
    ----------
    records: List[dict]

    delimiter: str
        Default '.'

    flatten_lists: bool
        Default False

    Returns
    -------
    List[dict]
        Flattened records.
    """
    if not isinstance(records, list):
        raise TypeError(
            f"Value for `records` must be a list. Received type: {type(records)}"
        )

    flatten_func = functools.partial(
        flatten_dict, delimiter=delimiter, flatten_lists=flatten_lists
    )

    return list(map(flatten_func, records))
