import functools
from typing import Any, List, Optional

import numpy as np
from flatten_dict import flatten, unflatten
from flatten_dict.reducers import make_reducer


def check_delimiter_collisions(obj: dict, delimiter: str, path: str = "") -> List[str]:
    """
    Recursively check for keys containing the delimiter character.
    
    Parameters
    ----------
    obj : dict
        Dictionary to check for delimiter collisions
    delimiter : str
        The delimiter character to check for
    path : str
        Current path (for recursive calls)
    
    Returns
    -------
    List[str]
        List of paths where delimiter collisions were found
    """
    collisions = []
    
    for key, value in obj.items():
        current_path = f"{path}{delimiter}{key}" if path else key
        
        if delimiter in key:
            collisions.append(current_path)
        
        if isinstance(value, dict):
            collisions.extend(check_delimiter_collisions(value, delimiter, current_path))
    
    return collisions


def get_nested_field_direct(obj: dict, field: str, delimiter: str = ".") -> Any:
    """
    Retrieves a nested field by traversing the dictionary structure directly.
    Does not use flattening, preserving keys that contain the delimiter.
    
    Parameters
    ----------
    obj : dict
        Dictionary to traverse
    field : str
        Field path using delimiter notation (e.g., "a.b.c")
    delimiter : str
        Delimiter to split the field path
    
    Returns
    -------
    Any
        The value at the nested path, or None if not found
    """
    # First check if the field exists as a literal key
    if field in obj:
        return obj[field]
    
    # Otherwise, traverse the nested structure
    parts = field.split(delimiter)
    current = obj
    
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    
    return current


def set_nested_field_direct(obj: dict, field: str, value: Any, delimiter: str = ".") -> None:
    """
    Sets a nested field by creating the nested structure directly.
    Does not use flattening/unflattening.
    
    Parameters
    ----------
    obj : dict
        Dictionary to modify (modified in place)
    field : str
        Field path using delimiter notation (e.g., "a.b.c")
    value : Any
        Value to set at the nested path
    delimiter : str
        Delimiter to split the field path
    """
    parts = field.split(delimiter)
    current = obj
    
    # Navigate/create the nested structure
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            # Can't traverse further if we hit a non-dict value
            return
        current = current[part]
    
    # Set the final value
    current[parts[-1]] = value


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
