Advanced Topics
###############

.. _custom-config-models:

Extending BackendConfig
=======================

``BackendConfig`` is a Pydantic ``BaseModel`` and can be subclassed to add domain- or capability-specific fields to
an Inference Backend. The example below extends ``BackendConfig`` and sets the subclass as the
``backend_config_model`` class attribute on a custom backend:

.. literalinclude:: ../code-examples/usage/extending-config-model.py
   :language: python
   :linenos:
   :emphasize-lines: 6-11,18,27

Config fields are accessed via the ``self.config`` instance attribute.

.. note::

    ``BackendConfig`` subclasses are validated according to `Pydantic's validation rules`_. In the example above,
    ``output_class_names`` has no default, so Pydantic treats it as required. Any instance of ``CustomBackend``
    must supply it — either as a keyword argument at instantiation time or via the ``backend_config:`` section of
    ``packflow.yaml`` when loading through ``InferenceBackendLoader.from_project()``:

    .. code-block:: python

        # Direct instantiation
        backend = CustomBackend(output_class_names=["doubled"])

        # Via packflow.yaml backend_config: + from_project()
        # packflow.yaml:
        #   backend_config:
        #     output_class_names: [doubled]
        backend = InferenceBackendLoader.from_project(".")

    .. _Pydantic's validation rules: https://docs.pydantic.dev/latest/concepts/models/#basic-model-usage


.. _configuration-sources:

Configuration Sources
=====================

The ``InferenceBackend`` in Packflow loads and validates configurations in the following priority order (lowest to highest):

1. Base Config defaults
    - Default values defined in ``BackendConfig`` or a custom subclass.
2. ``backend_config:`` values from ``packflow.yaml``
    - Applied only when a project is loaded via ``InferenceBackendLoader.from_project()``. Standalone loaders
      (``LocalLoader``, ``ModuleLoader``) do not read ``packflow.yaml`` and skip this level entirely.
3. Explicit keyword arguments passed at load time
    - Accepted by all loader methods (``.load()``, ``from_project()``). These always override both defaults and
      any ``backend_config:`` values.

All configurations are validated through Pydantic at load time.

Configuring the Backend via ``packflow.yaml``
=============================================

Project-level backend configuration is specified in the ``backend_config:`` section of ``packflow.yaml``.
These values are applied automatically when a project is loaded via ``InferenceBackendLoader.from_project()``,
making them well-suited for deployment-time configuration that should not be hardcoded into the backend itself —
such as environment-specific field names, feature lists, or preprocessor settings.

For example, if the input field names differ between the training environment and production, the mapping can be
declared in ``packflow.yaml`` without modifying the Inference Backend code:

.. code-block:: yaml

    # === BACKEND CONFIG ===
    backend_config:
      feature_names:
        - input_0
        - input_1

.. code-block:: python

    from packflow.loaders import InferenceBackendLoader

    backend = InferenceBackendLoader.from_project(".")
    backend({"input_0": 1.0, "input_1": 2.0})

This approach also works with custom ``BackendConfig`` subclasses — any field defined on the subclass can be
supplied via ``backend_config:`` in the same way.

Creating Reusable Backends
==========================

An Inference Backend packaged as an installable Python module can be shared and loaded across multiple
projects using ``ModuleLoader`` or by setting ``loader: module`` in ``packflow.yaml``. The ``backend_config:``
section in each project's ``packflow.yaml`` can then supply different configuration values to the same backend
without modifying its code. See the :ref:`Packflow Loaders<packflow-framework>` section for details.

.. _logging-configuration:

Logging Configuration
=====================

Packflow uses the `loguru <https://github.com/Delgan/loguru>`_ library for logging and defaults to the ``INFO`` log level to minimize noise in production environments. The log level can be controlled via the ``PACKFLOW_LOG_LEVEL`` environment variable.

Setting the Log Level
---------------------

To change the log level, set the ``PACKFLOW_LOG_LEVEL`` environment variable to one of the following values:

*   ``DEBUG``: Detailed diagnostic information useful for troubleshooting
*   ``INFO``: General informational messages (default)
*   ``WARNING``: Warning messages for potentially problematic situations
*   ``ERROR``: Error messages for serious problems
*   ``CRITICAL``: Critical messages for very serious errors

**Example:**

.. code-block:: bash

    # Enable debug logging for detailed diagnostics
    export PACKFLOW_LOG_LEVEL=DEBUG
    python inference.py

    # Use warning level to see only warnings and errors
    export PACKFLOW_LOG_LEVEL=WARNING
    python inference.py

.. note::

    The ``verbose`` field in the ``BackendConfig`` controls whether execution metrics are logged during inference. This is separate from the overall log level and defaults to ``False``. Set ``verbose=True`` to enable metrics logging.
