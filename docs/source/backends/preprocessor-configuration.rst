.. _backend-configuration:

Backend Configuration
#####################

The ``BackendConfig`` model controls preprocessing behavior, runtime logging, and output metadata for an Inference
Backend. It is set as the ``backend_config_model`` class attribute on the backend and accessed via the ``config``
instance attribute.

The following fields are used for default behaviors of the Base Config Model:

- ``verbose``: A boolean indicating whether to output verbose logs (e.g. per-inference execution metrics). Defaults to False.
- ``input_format``:  A string specifying the preprocessor; one of ``'passthrough'``, ``'records'``, or ``'numpy'``. For details, see :ref:`Preprocessors<preprocessors>`.
- ``rename_fields``: A dictionary mapping of ``{"old_name": "new_name"}`` which will be renamed during ``'records'`` or ``'numpy'`` preprocessing.
- ``feature_names``: A list of feature names. If non-empty, acts as a preprocessing filter. Behavior varies between ``'records'`` and ``'numpy'`` preprocessors. Defaults to an empty list.
- ``flatten_nested_inputs``: A boolean indicating whether to flatten nested inputs. Defaults to False.
- ``flatten_lists``: A boolean indicating whether to also flatten lists when flattening nested inputs. Defaults to False.
- ``nested_field_delimiter``: A string indicating the delimiter for nested fields. Defaults to a period ('.').
- ``output_keys``: A list of the keys expected in each output record. This is **declarative metadata only** — it does not affect inference execution. When ``backend.validate()`` is called, a warning is emitted for any declared key absent from the outputs. Defaults to an empty list (no validation performed).

.. warning::
    When ``flatten_nested_inputs`` is ``False``, input keys containing ``nested_field_delimiter`` may result in incorrect nested structures or key collisions. For best results, ensure delimiters do not appear in record keys.

**Example**

Consider the following ``backend_config:`` section in ``packflow.yaml``:

.. code-block:: yaml

    # === BACKEND CONFIG ===
    backend_config:
      flatten_nested_inputs: true
      nested_field_delimiter: ":"
      rename_fields:
        "foo:bar": feature_1
        "fizz:buzz": feature_2
      feature_names:
        - feature_1
        - feature_2

and this ``InferenceBackend`` implementation that simply prints the data at each stage:

.. literalinclude:: ../code-examples/usage/print-backend.py
   :language: python
   :linenos:
   :emphasize-lines: 6-8, 12, 16, 24-25
   :caption: ``inference.py``

When the backend is loaded directly without a project configuration, the input from the ``__main__`` block ``{"foo": {"bar": 0, "baz": [1]}, "fizz": {"buzz": 2}}`` passes through unchanged:

.. code-block:: console

    $ python inference.py
    PrintBackend called with args: ({'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}},), kwargs: {}
    Transform Inputs received: [{'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}}]
    Execute received: [{'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}}]
    Final Output: {'result': {'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}}}

When the backend is loaded from the project (with the above ``backend_config:`` in ``packflow.yaml``), the input is transformed according to the preprocessor configuration:

.. code-block:: python

    from packflow.loaders import InferenceBackendLoader

    backend = InferenceBackendLoader.from_project(".")
    print("Final Output:", backend({"foo": {"bar": 0, "baz": [1]}, "fizz": {"buzz": 2}}))

.. code-block:: console

    Transform Inputs received: [{'feature_1': 0, 'feature_2': 2}]
    Execute received: [{'feature_1': 0, 'feature_2': 2}]
    Final Output: {'result': {'feature_1': 0, 'feature_2': 2}}

The input record has been flattened, filtered to only include the specified feature names, and renamed according to the ``backend_config:`` section. This demonstrates how the preprocessor configuration fields can be used to manipulate input data before it reaches the core logic of the InferenceBackend, allowing an InferenceBackend to be reused across different data schemas with minimal code changes.

Please see :ref:`Configuration Sources<configuration-sources>` for more details on how configurations are loaded and overridden.

.. _preprocessors:

Preprocessors
=============

Preprocessing occurs in tandem to the Inference Backend framework to assist with streamlining development. Each preprocessor relies on
different :ref:`Backend Configuration<backend-configuration>` fields. The following subsections outline the required fields and expected behaviors for each preprocessor.

Passthrough Preprocessor
------------------------

**Condition**: Used when ``input_format="passthrough"``.

**Expected Behaviors:**

- Input data is untouched and passed directly to the ``transform_inputs()`` method.

Records Preprocessor [Default]
------------------------------

**Condition**: Used when ``input_format="records"``.

**Expected Behaviors:**

- If ``rename_fields`` has a value:
    - The fields in incoming records will be renamed based on this mapping, prior to any other preprocessing steps.

- If ``feature_names`` is not empty:
    - The records will be filtered and sorted based on the values in this array.
    - This will drastically lower the size of the data passing through the pipeline, which can lead to performance boosts.

- If ``flatten_nested_inputs`` is True:
    - Nested events (e.g., ``{"foo": {"bar": 0}}``) will be 'flattened' to ``{"foo.bar": 0}``.
    - The value of the ``nested_field_delimiter`` config will determine the delimiter for the flattened fields (default: '.').
    - If ``flatten_lists`` is True:
        - The flattening will also include lists.
        - Example: ``{"foo": {"bar": [0, 1]}}`` will be flattened to ``{"foo.bar.0": 0, "foo.bar.1": 1}``

**Nested Path Access:**

When using delimiter notation in ``rename_fields`` or ``feature_names`` to access nested paths (e.g., ``"foo.bar"`` to access ``{"foo": {"bar": value}}``), the preprocessor will traverse the nested structure directly without flattening. If a key in the path does not exist, it will be silently skipped and not included in the output.

**Important:** When ``flatten_nested_inputs=False``, the preprocessor **never flattens** the input data. Keys containing the delimiter character are preserved exactly as they appear. Nested path access is performed via direct traversal of the dictionary structure.

**Example:**

.. code-block:: python

    config = BackendConfig(
        flatten_nested_inputs=False,
        nested_field_delimiter=".",
        feature_names=["a.b", "x"]
    )
    
    # Input with nested structure
    input_data = [{"a": {"b": 10}, "x": 5}]
    
    # Output preserves nested structure for accessed paths
    # Result: [{"a": {"b": 10}, "x": 5}]

**Delimiter Collision Detection:**

When using nested path access (delimiter notation in ``rename_fields`` or ``feature_names``) with ``flatten_nested_inputs=False``, the preprocessor will check for keys that contain the delimiter character. This prevents ambiguity between literal keys and nested paths.

.. code-block:: python

    config = BackendConfig(
        flatten_nested_inputs=False,
        nested_field_delimiter=".",
        feature_names=["a.b"]  # Nested path access
    )
    
    # Input has a key containing the delimiter - this will raise an error
    input_data = [{"field.name": 42, "a": {"b": 1}}]
    # PreprocessorRuntimeError: Keys containing the delimiter '.' were found: ['field.name']

To bypass this check (not recommended), set ``ignore_delimiter_collisions=True``:

.. code-block:: python

    config = BackendConfig(
        flatten_nested_inputs=False,
        nested_field_delimiter=".",
        feature_names=["a.b"],
        ignore_delimiter_collisions=True  # Bypass collision detection
    )

.. warning::
    Setting ``ignore_delimiter_collisions=True`` may result in undefined behavior if key collisions occur. Use with caution and ensure your data does not contain keys with the delimiter character when using nested path access.

.. note::
    The default ``BackendConfig`` values will not trigger any of the above conditions and will fall back to acting as a
    Passthrough preprocessor for optimization purposes.

Numpy Preprocessor
------------------

**Condition**: Used when ``input_format="numpy"``.

**Expected Behaviors:**

- If ``rename_fields`` has a value:
    - The fields in incoming records will be renamed based on this mapping, prior to conversion to an ndarray.
    - Especially helpful if input names to not match required feature names.
- Creates a loosely-typed ``ndarray`` based on the contents of the ``feature_names`` config.
    - Example: If ``inputs=[{"foo": 0}, {"foo": 1}]`` and ``feature_names=["foo"]``, the data passed to ``transform_inputs()`` would be equivalent to ``numpy.array([[0], [1]])``.
