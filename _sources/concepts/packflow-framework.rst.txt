.. _packflow-framework:

Packflow Inference Backend
##########################

The ``packflow`` package introduces a flexible approach to building and deploying models and analyzers with its
**Inference Backend** architecture. The ``InferenceBackend`` is an abstract base class
that empowers developers to craft bespoke inference code or extend it to create reusable model backends.

Each Inference Backend has a ``BackendConfig`` that can be used to leverage out-of-the-box functionality and can be
extended to support more advanced, bespoke use-cases.

Lifecycle Functions
--------------------

When managing a model or analytic, there are often steps that relate to preparing resources for execution.
A common example would be loading a large model from a file or many files into memory, or moving a model loaded into memory to VRAM (the GPU memory).

Packflow's ``InferenceBackend`` provides the following functions to manage these steps:

1. **Initialization:** ``initialize()`` [Optional]
    - Optional user-defined method that runs during the ``InferenceBackend`` base class's ``__init__`` method.
    - **This is where model initialization logic should be defined.** Expensive or slow procedures related to initial model loading or preparation belong here (e.g., loading model weights from disk, moving models to GPU memory, initializing connections to external services).
    - **It is NOT recommended** to extend the ``__init__`` method in order to define model initialization logic. The ``initialize()`` method is included in profiling calculations, and the ``__init__`` method runs without profiling to load configurations, set up the logger and preprocessor, and set up the profiling metrics.
    
    .. admonition:: Example Use Case
    
        A deep learning model requires loading a 2GB PyTorch model file and moving it to GPU memory. This operation takes 5-10 seconds. By implementing this logic in ``initialize()``, the initialization time is automatically profiled and logged, helping identify deployment bottlenecks. If this were done in ``__init__`` instead, the timing wouldn't be captured in metrics, making it harder to diagnose slow startup times in production.
    
    .. note::
    
        When overriding ``__init__``, ``super().__init__(**kwargs)`` must be called to preserve base class behavior (configuration loading, logger setup, preprocessor setup, and profiling metrics). For example:
        
        .. code-block:: python
        
            def __init__(self, custom_param, **kwargs):
                super().__init__(**kwargs)  # Required!
                self.custom_param = custom_param
    
2. **Readiness check:** ``ready()`` [Optional]
    - Optional user-defined method that can be implemented to signal whether the analytic is ready to accept execution requests.
    - Packflow provides the ``ready()`` method interface but does not enforce or check it internally. Calling ``backend(data)`` will always attempt execution regardless of what ``ready()`` returns. This method exists for external systems (e.g., orchestration platforms, health check endpoints, monitoring dashboards) to query readiness status before attempting execution.
    - Useful for use cases where initialization occurs in the background or depends on external resources not managed by the Inference Backend.
    
    .. admonition:: Example Use Case
    
        An Inference Backend depends on an external API that may be temporarily unavailable. Implement ``ready()`` to check the API connection. A Kubernetes readiness probe can call ``backend.ready()`` to control traffic routing - if it returns ``False``, no traffic is routed to that instance. Note that direct calls to ``backend(data)`` will still execute regardless of readiness status.


Execution Functions
--------------------

Execution of an Inference Backend consists of four primary steps, each serving a distinct purpose:

1. **Preprocessing:** [Internal]
    - Inference Backends have built-in preprocessing steps to assist in common data transformation steps.
    - Preprocessors will run automatically based on the ``input_format`` field of the ``BackendConfig``.
    - Supported preprocessors:
        - ``passthrough``: Gives most flexibility by directly passing the data through without any preprocessing.
        - ``records`` [Default]: Provides the ability to rename, filter, or flatten nested fields on input data.
            - *Note: This preprocessor acts as a passthrough until specific fields are explicitly set.*
        - ``numpy``: Converts input records to a Numpy NDArray
    - See the :ref:`Preprocessors<preprocessors>` section of the documentation for more details on each processor.

2. **Input Transformation:** ``transform_inputs()`` [Optional]
    - An optional, user-defined method to transform inputs and return featurized/model-ready data.
    - If the method is not defined, preprocessed data is passed directly through to the ``execute()`` method.

3. **Model Execution:** ``execute()`` [Required]
    - Required user-defined method that performs model inference, analysis, or other operations that generate outputs.
    - This step should focus on the main execution logic with minimal pre- or post-processing.

4. **Output Transformation:** ``transform_outputs()`` [Optional]
    - Optional user-defined method to apply business logic, calculate metrics, and perform data type conversions as necessary.
    - If the method is not defined, the result of ``execute()`` is passed through as the final output.


**Execution Procedure**

All data passed through the Inference Backend follows a direct execution of:

.. code-block:: text

    inputs --> preprocess --> transform_inputs --> execute --> transform_outputs --> outputs

As ``transform_inputs`` and ``transform_outputs`` are optional, the final execution could take the following forms:

.. code-block:: text

    Backend with only ``execute()`` defined:
        inputs --> preprocess --> execute --> outputs

    Backend with ``transform_inputs()`` and ``execute()`` defined:
        inputs --> preprocess --> transform_inputs --> execute --> outputs

    Backend with ``execute()`` and ``transform_outputs()`` defined:
        inputs --> preprocess --> execute --> transform_outputs --> outputs

The inputs to a Packflow Inference Backend will **always** be records (e.g., a list of dictionaries). As such, the
*final output* of the Inference Backend must also be in the records format. More specifically, this means the
**final step** must meet the API requirement, whether the final defined step is ``execute()`` or ``transform_outputs()``.
Intermediate steps (e.g., transfer between ``transform_inputs()`` and ``execute()``) can be any data format.


**The Power of Modular Design**

The separation into each distinct step is driven by the need for **profiling and optimization**. By isolating each
phase, ``packflow`` automatically tracks key metrics such as execution time for each step, facilitating the identification
of bottlenecks and areas for improvement. These valuable insights are not only logged with each backend call but also
accessible programmatically through the ``.get_metrics()`` method, empowering developers to optimize and refine their
Inference Backends continuously.

.. admonition:: Example

    An Inference Backend is deployed to production and it is observed that there is comparatively high latency in
    the ``transform_inputs()`` step. After investigation, it was found that preprocessing was much faster when using Numpy
    instead of Pandas for formatting the data prior to inference. Upon deploying again, it is observed that latency was
    lowered.


Packflow Loaders
----------------

Packflow provides two distinct approaches to loading an Inference Backend. Each serves a different context and carries
different responsibilities.

Standalone Loading
~~~~~~~~~~~~~~~~~~

``LocalLoader`` and ``ModuleLoader`` are project-agnostic. They locate and instantiate an Inference Backend from a
Python module path without reading ``packflow.yaml`` or applying any project-level configuration. The backend is
configured entirely through its own defaults and any keyword arguments supplied at load time.

``LocalLoader`` resolves the module path relative to the current working directory. It is well-suited for
development workflows, Jupyter Notebooks, and scripts where a formal packflow project structure is not required:

.. code-block:: python
    :caption: ``LocalLoader`` — standalone script or notebook

    from packflow.loaders import LocalLoader

    backend = LocalLoader('inference:Backend').load()
    backend({"sample": "data"})

``ModuleLoader`` loads from an installed Python package. It is the appropriate choice when the Inference Backend is
distributed as a package (e.g., via a private PyPI repository) and the consumer has installed it with a tool such as
``pip``, ``poetry``, or ``uv``:

.. code-block:: python
    :caption: ``ModuleLoader`` — installed package

    from packflow.loaders import ModuleLoader

    backend = ModuleLoader('myproject.backends:MyModelBackend').load()
    backend({"sample": "data"})

Because neither loader reads ``packflow.yaml``, project-level configuration — ``backend_config:``, ``env:``, and
``output_keys`` — is not applied automatically. Backend configuration must be supplied explicitly as keyword arguments:

.. code-block:: python

    backend = LocalLoader('inference:Backend').load(
        feature_names=["input_0", "input_1"],
        verbose=True,
    )

Alternatively, if a ``packflow.yaml`` is available but a specific loader is needed, the config can be read explicitly
and the ``backend_config`` section passed through:

.. code-block:: python

    from packflow.loaders import LocalLoader
    from packflow.loaders.config import PackflowConfig

    config = PackflowConfig.from_project_path(".")
    backend = LocalLoader(config.inference_backend).load(**config.backend_config)

Project-Aware Loading
~~~~~~~~~~~~~~~~~~~~~

``InferenceBackendLoader.from_project()`` reads ``packflow.yaml`` from a project directory and applies its
configuration before loading the backend. Specifically, it:

- Applies any ``env:`` variables to the process environment.
- Selects the loader type (``local`` or ``module``) as specified by the ``loader:`` field.
- Passes the ``backend_config:`` section as the base configuration for the backend.

.. code-block:: python
    :caption: ``InferenceBackendLoader.from_project()`` — project directory

    from packflow.loaders import InferenceBackendLoader

    backend = InferenceBackendLoader.from_project(".")
    backend({"sample": "data"})

Explicit keyword arguments passed to ``from_project()`` are merged on top of ``backend_config:`` values, so
per-call overrides are still possible:

.. code-block:: python

    backend = InferenceBackendLoader.from_project(".", verbose=True)

See the :ref:`Configuration Sources<configuration-sources>` section for full details on how configuration values are merged
and validated.

.. note::

    ``ModuleLoader`` is the loader type used when ``loader: module`` is set in ``packflow.yaml``. See the
    **Scikit-Learn Classifier** notebook in the :ref:`Examples<examples>` section for a complete walkthrough of
    creating a pip-installable package with a Packflow backend.
