from random import randint

from packflow import load_inference_backend, validate_inference_backend


if __name__ == "__main__":
    # -- Load the Inference Backend --
    backend = load_inference_backend(project_path=".")

    # -- Generate sample data --
    batch = [
        {"a": randint(0, 100), "b": randint(0, 100), "c": randint(0, 100)}
        for _ in range(5)
    ]

    event = batch[0]

    # -- Run Validations --
    print("Event Output:", validate_inference_backend(backend, event))
    print("Batch Output:", validate_inference_backend(backend, batch))
