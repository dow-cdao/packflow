# Import Packflow's dev tools to run validations on the Inference Backend
from packflow.loaders import LocalLoader

# Load the backend in the current directory
# The path 'inference:Backend' can be interpreted as
#   `from inference import Backend`
backend = LocalLoader("inference:Backend").load()

# Define sample inputs that represent realistic data for your backend.
# These should exercise the expected input format(s) your backend will receive.
SAMPLE_SINGLE_ROW = {"number": 5}

SAMPLE_BATCH = [
    {"number": 5},
    {"number": 10},
    # Add more sample rows as needed
]

if __name__ == "__main__":
    print("Running validation...")

    print(f"Sample single row: {SAMPLE_SINGLE_ROW}\n")
    print(f"Sample batch: {SAMPLE_BATCH}\n")

    # backend.validate() runs your backend and checks the outputs
    # meet Packflow's API requirements. Returns outputs if valid.
    outputs_single_row = backend.validate(SAMPLE_SINGLE_ROW)
    outputs_batch = backend.validate(SAMPLE_BATCH)

    print(f"Outputs single row: {outputs_single_row}")
    print(f"Outputs batch: {outputs_batch}")
    print("\nValidation passed!")
