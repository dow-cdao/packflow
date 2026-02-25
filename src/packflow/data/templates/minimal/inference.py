from typing import Any, List

from packflow import InferenceBackend


class Backend(InferenceBackend):
    def transform_inputs(self, inputs: List[dict]) -> Any:
        """Preprocessing steps or other transformations before running inference.

        This function should ingest raw records and return inference-ready features.
        Ex: [{"foo": 5}] -> np.array([[5]])

        Parameters
        ----------
        inputs: List[Dict]
            A list of dictionary objects

        Returns
        -------
        Any
            The expected input data for the model or function is.

        Notes
        -----
        This function should *not* filter rows. The input and output batches should
        have the same length.
        """
        return inputs

    def execute(self, inputs: Any) -> Any:
        """The main execution of inference or analysis for the developed application.

        This method should remain targeted to passing data through the model/execution
        code for profiling purposes. Minimal pre- or post-processing should occur at this
        step unless completely necessary.

        Parameters
        ----------
        inputs: List[Dict]
            The output of the transform_inputs method. If the transform_inputs method is
            not overridden, the data is formatted as records (list of dictionaries)

        Returns
        -------
        Any
            Model Outputs

        Notes
        -----
        The transform_outputs() method should handle all postprocessing including calculating
        metrics, converting outputs back to Python types, and other postprocessing steps. Try
        to keep this method focused purely on inference/analysis.
        """
        raise NotImplementedError

    def transform_outputs(self, outputs):
        """Postprocessing steps or other transformation steps to be executed prior to
        returning outputs.

        Parameters
        ----------
        outputs: Any
            The output of the execute method.

        Returns
        -------
        List[dict]
            Model Outputs

        Notes
        -----
        The transform_outputs() method *must* output json-serializable data in the form of
        records (a list of dictionaries).
        """
        return outputs
