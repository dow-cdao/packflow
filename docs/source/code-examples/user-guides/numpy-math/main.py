from packflow import InferenceBackend


class NumpyMath(InferenceBackend):
    def execute(self, inputs):
        """
        Receives the input array from transform_inputs and calculates the mean.
        """
        means = inputs.mean(axis=1)

        return means

    def transform_outputs(self, outputs):
        """
        Use Packflow utilities to convert outputs to native Python types
        """
        return [
            # calling tolist() on a numpy array converts to native Python types
            {"mean": v}
            for v in outputs.tolist()
        ]


# Set Default Arguments for the NumpyMath backend
app = NumpyMath(feature_names=["a", "b", "c"], input_format="numpy")
