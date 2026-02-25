.. _custom-backends:

Creating a Custom Backend
=========================

The Inference Backend class provides a flexible pipeline for executing machine learning models. The pipeline consists of several steps, each 
with its own purpose.

Initialize
----------

The Packflow framework will handle most initialization, such as loading and validating configurations. The ``initialize()`` step
is an optional method that is called when the Inference Backend is being set up. Therefore, this step is reserved for Inference Backend-specific
logic (e.g., loading model weights or one-time setup code).


.. code-block:: python

    from packflow import InferenceBackend

    class Backend(InferenceBackend):
        def initialize(self, *args, **kwargs):
            self.logger.info("Loading model weights")
            self.logger.info("Placing model on GPUs")
            # ... etc

Preprocess
----------

A preprocessing step, separate from the user-defined ``transform_inputs()`` step, can be configured using a :ref:`Backend Configuration<backend-configuration>`.
To understand the available preprocessors, see :ref:`Preprocessors<preprocessors>`.


Transform Inputs
----------------

The ``transform_inputs()`` step is an optional method that ingests preprocessed data and returns its outputs to the
``execute()`` method. 

**Input**: Specified by the ``input_format`` and could be any raw inputs, preprocessed records, or a numpy array.

**Output**: Fully transformed, model-ready features.

Execute
-------


The ``execute()`` step is an **required** method that ingests transformed inputs and returns its model outputs/results
to the ``transform_outputs()`` method. There should be minimal pre- or post-processing done in this step to ensure latency
profiling is accurate.

**Input**:
1. The output of the ``preprocess`` step if ``transform_outputs()`` **is not defined**, or
2. The output of the ``transform_outputs()`` method.

**Output**: Model outputs or results. 

.. warning::
    If the ``transform_outputs()`` step is unused, it **must** return results that meet Packflow's
    :ref:`Validation<validation>` requirements.

Transform Outputs
-----------------
The ``transform_outputs()`` step is an optional method that ingests the outputs of ``execute()`` and returns the final
pipeline output.

**Input**: The direct output of ``execute()``.

**Output**: Clean outputs with business logic or labeling applied for downstream consumers to
ingest. The outputs of this method **must** return results that meet Packflow's :ref:`Validation<validation>` requirements.

Best Practices
--------------
- Assume that data flowing through the pipeline may originate from multiple replicas and may not be in order.
- Ensure that the output of the transform_inputs method is in a format that can be processed by the execute method.
- Use the transform_outputs method to apply business logic and convert the model's output into a JSON-serializable format.
