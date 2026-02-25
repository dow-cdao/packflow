.. _validation:

Validation
##########

This documentation provides information on Packflow's built-in validation tools for Inference Backends and how to use them effectively during development.

Rules
=====

Packflow's validators enforce a series of rules to ensure fully normalized inputs/outputs. For reference, the rules are listed
below:

- **Correct Input Format:**
    - Inputs must be provided as a dictionary or a list of dictionaries.
- **Inputs and Outputs are same length:**
    - The number of inputs rows *must* match in length.
    - *Tip:* Build in exception handling and return an empty dictionary if a row fails, when possible
- **Correct Output Format:**
    - The output type must match the input type (e.g., dictionary in, dictionary out)
- **Outputs must be JSON Serializable:**
    - Output cannot contain non-native types (e.g., Numpy Arrays) that are not serializable with the ``json`` library.

Packflow's built-in validation helpers check these rules and will warn if some conditions are not met -- however, it is
recommended to keep these items in mind when developing.

Running Validations
===================

Use the Inference Backend's built-in ``.validate()`` method to run all validation checks against sample input data.

This can be accomplished programmatically:

.. code-block:: python
   :linenos:

    # -- Import backend --
    from main import Backend

    backend = Backend()

    # Replace this with data relevant to the Inference Backend implementation
    sample_data = {"number": 5}

    outputs = backend.validate(sample_data)

    # If all validations passed, the outputs will be returned and can be visually inspected
    print(outputs)

Best Practices
==============

.. _best-practices-testing:

To ensure effective testing and validation for an Inference Backend, consider the following best practices:

- **Use realistic sample data:** When running validations, use sample data that closely resembles the expected input during actual inference.
- **Write unit tests:** While Packflow provides validation of Inference Backend input/output, these validation checks are best used alongside a proper unit testing framework, such as ``pytest`` or ``unittest``, rather than as a replacement. Packflow's validation tools can be integrated with established unit tests to ensure the Inference Backend consistently meets the required standards.

.. warning::
    Packflow's validation checks run only when explicitly invoked via the ``.validate()`` method. They do not run automatically during inference, i.e. in ``.__call__()`` or any other pipeline method. It is the developer's responsibility to ensure that the Inference Backend is validated as needed and when changes are made. This is one reason why integrating validation checks into unit tests is recommended.

Next Steps
==========

Continue to the :ref:`Preparing for Distribution<distribution>` documentation page for instructions on how to prepare a Packflow project that can be shared across environments for replicable inference.
