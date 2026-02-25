Configuring the Preprocessor
############################

.. _backend-configuration:

Backend Configuration
=====================

The base ``BackendConfig`` contains fields that are leveraged by internal functions for processing input data prior 
to passing inputs to the ``transform_inputs()`` method. The base config arguments are initialized at the Backend's
``base_config_model`` class attribute, and they can be accessed via the ``config`` instance attribute in the custom
Inference Backend.

The following fields are used for default behaviors of the Base Config Model:

- ``verbose``: A boolean indicating whether to output verbose logs. Defaults to True.
- ``input_format``:  A string specifying the preprocessor; one of ``'passthrough'``, ``'records'``, or ``'numpy'``. For details, see :ref:`Preprocessors<preprocessors>`.
- ``rename_fields``: A dictionary mapping of ``{"old_name": "new_name"}`` which will be renamed during ``'records'`` or ``'numpy'`` preprocessing.
- ``feature_names``: A list of feature names. If non-empty, acts as a preprocessing filter. Behavior varies between ``'records'`` and ``'numpy'`` preprocessors. Defaults to an empty list.
- ``flatten_nested_inputs``: A boolean indicating whether to flatten nested inputs. Defaults to False.
- ``flatten_lists``: A boolean indicating whether to also flatten lists when flattening nested inputs. Defaults to False.
- ``nested_field_delimiter``: A string indicating the delimiter for nested fields. Defaults to a period ('.').

.. warning::
    When ``flatten_nested_inputs`` is ``False``, input keys containing ``nested_field_delimiter`` may result in incorrect nested structures or key collisions. For best results, ensure delimiters do not appear in record keys.

**Example**

Consider the following preprocessor configuration:

.. literalinclude:: ../code-examples/usage/example-config.json
   :language: json
   :linenos:
   :caption: ``/path/to/a/config.json``

and this ``InferenceBackend`` implementation that simply prints the data at each stage:

.. literalinclude:: ../code-examples/usage/print-backend.py
   :language: python
   :linenos:
   :emphasize-lines: 6-8, 12, 16, 24-25
   :caption: ``inference.py``

When the above backend is executed without configuration, the input from the ``__main__`` block ``{"foo": {"bar": 0, "baz": [1]}, "fizz": {"buzz": 2}}`` will pass through unchanged:

.. code-block:: console

    $ python inference.py
    PrintBackend called with args: ({'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}},), kwargs: {}
    Transform Inputs received: [{'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}}]
    Execute received: [{'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}}]
    Final Output: {'result': {'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}}}

However, when the backend is executed with the above config, the input will be transformed according to the preprocessor configuration:

.. code-block:: console

    $ BACKEND_CONFIG_FILE_PATH=/path/to/a/config.json python inference.py
    PrintBackend called with args: ({'foo': {'bar': 0, 'baz': [1]}, 'fizz': {'buzz': 2}},), kwargs: {}
    Transform Inputs received: [{'feature_1': 0, 'feature_2': 2}]
    Execute received: [{'feature_1': 0, 'feature_2': 2}]
    Final Output: {'result': {'feature_1': 0, 'feature_2': 2}}

The input record has been flattened, filtered to only include the specified feature names, and renamed according to the config file. This demonstrates how the preprocessor configuration fields can be used to manipulate input data before it reaches the core logic of the InferenceBackend, allowing for an InferenceBackend to be reused across different data schemas with minimal code changes.

Please see :ref:`Config Hierarchy<config-hierarchy>` for more details on how configurations are loaded and overridden.

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
