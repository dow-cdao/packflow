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
    - Expensive or slow procedures related to initial model loading or preparation belong here.
    - **It is NOT recommended** to extend the ``__init__`` method in order to define model initialization logic. The ``initialize()`` method is included in profiling calculations, and the ``__init__`` method runs without profiling to load configurations, set up the logger and preprocessor, and set up the profiling metrics.
    
2. **Readiness check:** ``ready()`` [Optional]
    - Optional user-defined method to define whether the Packflow analytic is ready to accept execution requests.
    - Packflow does not check readiness before allowing calls to ``backend.__call__(...)``, ``backend.execute(...)``, etc; Intended for use by third party systems that wish to check/report readiness, hold off on attempting execution, and so forth.
    - Intended for use cases where initialization occurs in the background or depends on other resources not managed by the Inference Backend.


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

Packflow includes integrations for loading Inference Backends from standalone scripts (``LocalLoader``) or packages
installed with tools such as ``poetry`` or ``uv`` (``ModuleLoader``). This flexibility enables developers to integrate
``packflow`` into existing Python packages or use it in a more informal setting like Jupyter Notebooks or Conda
environments to write, validate, and share inference code without any packaging frameworks.

.. code-block:: python
    :caption: ``LocalLoader`` Example

    from packflow.loaders import LocalLoader

    backend = LocalLoader('inference:Backend').load()

    backend({"sample": "data"})
    # >> {"sample": "data"}
