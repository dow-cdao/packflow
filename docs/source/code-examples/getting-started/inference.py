from typing import Any, List

from packflow import InferenceBackend


class Backend(InferenceBackend):
    def transform_inputs(self, inputs: List[dict]) -> Any:
        """
        Preprocessing steps or other transformations before running inference.
        ...
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
        outputs = []
        for row in inputs:
            outputs.append({"doubled": row["number"] * 2})

        return outputs

    def transform_outputs(self, outputs):
        """
        Postprocessing steps or other transformation steps to be executed prior to
        returning outputs.
        ...
        """
        return outputs
