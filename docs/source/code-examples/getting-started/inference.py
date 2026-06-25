from packflow import InferenceBackend


class Backend(InferenceBackend):
    def execute(self, inputs):
        outputs = []
        for row in inputs:
            outputs.append({"doubled": row["number"] * 2})
        return outputs
