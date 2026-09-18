.. _validation:

I/O Format Checking
###################

``backend.check_io()`` runs the backend against sample input and checks that the outputs meet Packflow's format requirements: correct types, matching row counts, and JSON-serializable values. If all checks pass, the outputs are returned for inspection.

The optional ``tests.py`` file included in generated projects contains a ``test_check_io`` test that calls ``backend.check_io()`` with sample data. Update the sample inputs to match the backend's expected input format before running.

Rules
=====

Packflow's validators enforce a series of rules to ensure fully normalized inputs/outputs. For reference, the rules are listed
below:

- **Correct Input Format:**
    - When calling ``check_io()`` or invoking a backend directly, inputs may be provided as a single dictionary or a list of dictionaries. Single-dictionary inputs are normalized to a list by the framework before reaching the backend.
    - The pipeline entry-point (``transform_inputs`` if defined, otherwise ``execute``) receives a **list of dictionaries** for ``passthrough`` and ``records`` preprocessors, or an ``ndarray`` for ``numpy``. Preprocessing still runs during ``.check_io()`` - data reaches the entry-point in the format determined by ``input_format``.
- **Inputs and Outputs are same length:**
    - The number of output dictionaries must equal the number of input dictionaries.
    - *Tip:* Build in exception handling and return an empty dictionary if a row fails, when possible
- **Correct Output Format:**
    - The final pipeline step (``transform_outputs`` if defined, otherwise ``execute``) must return a **list of dictionaries** equal in length to the input list. Intermediate steps may pass data in any format.
- **Outputs must be JSON Serializable:**
    - Output cannot contain non-native types (e.g., Numpy Arrays) that are not serializable with the ``json`` library.

Packflow's built-in validation helpers check these rules and will warn if some conditions are not met -- however, it is
recommended to keep these items in mind when developing.

.. seealso::

    :ref:`Packflow Inference Backend <packflow-framework>` - for a full explanation of the pipeline I/O contract, including how single-dict inputs are handled at the framework level and where list-of-dict is required.

Running I/O Format Checks
=========================

Use the Inference Backend's built-in ``.check_io()`` method to run all format checks against sample input data.

This can be accomplished programmatically:

.. code-block:: python
   :linenos:

    # -- Import backend --
    from main import Backend

    backend = Backend()

    # Replace this with data relevant to the Inference Backend implementation
    sample_data = {"number": 5}

    outputs = backend.check_io(sample_data)

    # If all checks passed, the outputs will be returned and can be visually inspected
    print(outputs)

Best Practices
==============

.. _best-practices-testing:

- **Use realistic sample data:** When running I/O format checks, use sample data that closely resembles the expected input during actual inference.
- **Integrate with unit tests:** Packflow's format checks are most effective when run alongside tests written for the backend's expected behavior.

.. warning::
    Packflow's format checks run only when explicitly invoked via the ``.check_io()`` method. They do not run automatically during inference, i.e. in ``.__call__()`` or any other pipeline method.

Next Steps
==========

Continue to the :ref:`Preparing for Distribution<distribution>` documentation page for instructions on how to prepare a Packflow project that can be shared across environments for replicable inference.
