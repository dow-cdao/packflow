Advanced Topics
###############

.. _custom-config-models:

Custom Config Models
====================

The ``BackendConfig`` is an implementation of a Pydantic ``BaseModel`` and can be extended to add more domain- or
capability-specific configurations to the Inference Backend.  Please see the example below in which the
``BackendConfig`` is extended and initialized as the ``CustomBackend``'s ``backend_config_model`` class attribute.


.. literalinclude:: ../code-examples/usage/extending-config-model.py
   :language: python
   :linenos:
   :emphasize-lines: 6-11,18,27

Further down, the config fields are accessed via the `self.config` instance attribute.

.. note::

    The ``BackendConfig`` will be interpreted and validated according to
    `Pydantic's validation rules`_.  In the example above, because the ``output_class_names`` field is required,
    Pydantic will treat it as such.  Therefore, any instances of ``CustomBackend`` must be initialized with the
    ``output_class_names`` keyword argument.  For example:

    ``backend = CustomBackend(output_class_names=["doubled"])``

    .. _Pydantic's validation rules: https://docs.pydantic.dev/latest/concepts/models/#basic-model-usage


.. _config-hierarchy:

Config Hierarchy
----------------

The ``InferenceBackend`` in Packflow automatically loads and validates configurations passed through three methods:

1. Base Config Arguments
    - These are the default values defined in the config.
2. Keyword Arguments Passed at Backend Load Time
    - These will override the base config values.
3. An optional JSON configuration file that will override all other configs
    - The Inference Backend will load this overrides file from a path passed through the ``BACKEND_CONFIG_FILE_PATH`` environment variable.

.. important::
    All configurations are Deep Merged, meaning only explicitly set fields will override fields.

    **Example:** If the base is ``{"parent": {"child_1": 1, "child_2": 2}}`` and the overrides are
    ``{"parent": {"child_2": 200, "child_3": 3}}``, then the deep-merged output will be ``{"parent": {"child_1": 1, "child_2": 200, "child_3": 3}}``


This approach ensures that configuration is not only easy, but robust through Pydantic validators to help
engineers tasked with deploying, debugging, and optimizing the production deployment.

Why Use a JSON Configuration File?
----------------------------------

An external JSON configuration file is especially helpful for custom configurations in production environments, which allow further
configuration of conditions change. For example, if the input fields in the lab/training environment are ``INPUT0`` and
``INPUT1`` but in production, they are ``input_0`` and ``input_1``, the config.json can be configured without changing
the code of the Inference Backend by creating the following file:

.. code-block:: json

    {
      "configs": {
        "feature_names": ["input_0", "input_1"]
      }
    }

Then setting the ``BACKEND_CONFIG_FILE_PATH`` environment variable to the absolute path to the config file:

.. code-block:: bash

    export BACKEND_CONFIG_FILE_PATH=/path/to/config.json

This will be automatically loaded and validated with the Inference Backend's config model.

.. important::

   The loaded JSON configuration file *must* contain a ``"configs"`` parent key or all values will be ignored. This
   behavior is the ensure the config file format is extensible to new fields in future releases of Packflow.

Example Use Cases
-----------------

Here are some example use cases for custom configuration models:

- Use Case #1: Dynamic Input Field/Feature Names
    - A machine learning model requires a specific set of features to be processed. - Create a custom configuration model that includes these features and use it to validate the input data.

- Use Case #2: Test/Prod Configurations
    - A data processing pipeline requires different configurations for different environments (e.g., development, testing, production). - Create custom configuration models for each environment and use them to configure the pipeline.

By using custom configuration models, code can be more flexible and easier to maintain.

Creating Reusable Backends
==========================

Inference Backends can be designed to be reusable across multiple projects. This approach allows sharing of common functionality and reducing duplication.

Benefits of Reusable Backends
-----------------------------

*   Write once, use many: A single reusable Inference Backend can support multiple projects that share similar requirements.
*   Simplified maintenance: Updates to the Inference Backend can be applied universally, reducing the effort needed to maintain multiple bespoke solutions.

Example: SklearnPipelineBackend
-------------------------------

For instance, organizations that frequently uses Scikit-Learn pipelines, can create a single ``SklearnPipelineBackend``. This Inference Backend can be configured to run multiple pipelines, leveraging:

*   **Backend configurations**: Specify key information like input names and types.
*   **Optimized inference code**: Reuse optimized code for inference, improving performance and reducing duplication.

Best Practices
--------------

*   **Modular design**: Design Inference Backends to be modular, making it easier to reuse and combine them.
*   **Flexible configuration**: Use configuration options to adapt the Inference Backend to work with different projects and requirements.
