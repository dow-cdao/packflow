from packflow import InferenceBackend


class PrintBackend(InferenceBackend):
    def __call__(self, *args, **kwargs):
        # Normally, __call__ should not be overridden in a backend.
        # This is just to show the inputs before the internal preprocessors run.
        print(f"PrintBackend called with args: {args}, kwargs: {kwargs}")
        return super().__call__(*args, **kwargs)

    def transform_inputs(self, inputs):
        print(f"Transform Inputs received: {inputs}")
        return inputs

    def execute(self, inputs):
        print(f"Execute received: {inputs}")
        # Config fields are available in the backend through self.config
        # For demonstration, this will just encapsulate each record in a dict with a "result" key.
        return [{"result": record} for record in inputs]


if __name__ == "__main__":
    backend = PrintBackend()
    sample_input = {"foo": {"bar": 0, "baz": [1]}, "fizz": {"buzz": 2}}
    print("Final Output:", backend(sample_input))
