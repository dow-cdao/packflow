# Import Packflow's dev tools to run validations on the Inference Backend
from packflow.loaders import LocalLoader

# Load the backend in the current directory
# The path 'inference:Backend' can be interpreted as
#   `from inference import Backend`
backend = LocalLoader("inference:Backend").load()

# Define sample inputs that represent realistic data for your backend.
# These should exercise the expected input format(s) your backend will receive.
SAMPLE_INPUTS = [
    {"example_field": "example_value"},
    # Add more sample rows as needed
]

if __name__ == "__main__":
    print("Running validation...")
    print(f"Sample inputs: {SAMPLE_INPUTS}\n")

    # backend.validate() runs your backend and checks the outputs
    # meet Packflow's API requirements. Returns outputs if valid.
    outputs = backend.validate(SAMPLE_INPUTS)

    print(f"Outputs: {outputs}")
    print("\nValidation passed!")
