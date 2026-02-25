def inference_backend_parts(path: str) -> list[str]:
    """
    Utility for splitting the inference_backend to the module and object parts

    Parameters
    ----------
    path : str
        The path to the backend to load. Notation should follow 'module.submodule:object'

    Returns
    -------
    list[str]
        Parts the first will be the path to the module and the second will be the object
        within the module that will be loaded.

    Example
    -------
    'foo.bar:baz' would return ['foo.bar', 'baz'] and can be interpreted as:
        from foo.bar import baz
    """
    parts = path.split(":")

    if len(parts) != 2:
        raise ValueError(
            "Path must contain exactly one colon separating module and object"
        )
    return parts
