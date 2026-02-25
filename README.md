<h1 style="text-align: center; border-bottom: none !important;">
  <img src="assets/packflow-logo-white-text.png" width="500" alt="Packflow logo">
</h1>

<p align="center">
  <a href="https://pypi.org/project/packflow/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/packflow.svg"></a>
  <a href="https://pypi.org/project/packflow/"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/packflow.svg"></a>
  <a href="https://github.com/dow-cdao/packflow/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg"></a>
</p>

# Introduction

`packflow` is a software development kit (SDK) that simplifies the development process and standardizes packaging of AI/ML
running on streaming data sources.

Many existing packaging frameworks are catered towards inference APIs and often require custom preprocessing steps. This can be particularly challenging when dealing with data sources that typically generate data one row at a time in key-value pairs (e.g., firewall logs or message streams).

Packflow, however, is optimized to run models on either individual events or batches of events, streamlining development and reducing the need for additional preprocessing. By leveraging Packflow, teams can focus on building and deploying models with custom out-of-the-box workflows and utilities, significantly reducing the time and effort required to onboard new capabilities.

## Getting Started

The following instructions quickly walk through how to install Packflow and serve user documentation.

### Installing Packflow

#### Prerequisite Requirements

- **Python** (version 3.10+)

#### Installation from PyPI

1. Packflow can be installed directly from PyPI:

```bash
pip install packflow
```

from the root of the Packflow repo.

> [!NOTE]
> If contributing to Packflow, it is recommended to install `packflow` from source in editable mode: `pip install -e .`

## Packflow Documentation

Packflow documentation is available pre-built in the repository and can be viewed immediately, or built from source for development work. Follow the instructions below to get started with serving the documentation.

### Viewing Pre-built Documentation

The simplest way to view the Packflow documentation is to serve the pre-built HTML files included in the repository:

1. Navigate to the pre-built docs folder: `cd docs/built/html`
2. Start a local web server: `python -m http.server 8000`
3. Access the documentation in a web browser by navigating to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

> [!WARNING]
> If a "Not Found" error page is received when first accessing the documentation, wait a moment for the server to fully start and refresh the page.

### Building Documentation from Source

#### Prerequisite Requirements

The following are required to build documentation from source:

- **Python** (version 3.10+)
- **Pip**
- **Packflow** (the version corresponding to the docs being served)
- **Pandoc**[^1] (see Pandoc.org's [official installation instructions](https://pandoc.org/installing.html))
- **`make` Command**[^2]

#### Steps

1. Navigate to the docs folder: `cd docs`
2. Install Python dependencies for building and hosting the documentation: `pip install -r requirements.txt`
3. Run `make dev` to serve the documentation from a working tree with live updates, or `make prod-serve` to serve static multi-version documentation (requires `.git` directory with branch/tag history)
4. Access the built documentation in a web browser by navigating to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

> [!WARNING]
> If a "Not Found" error page is received when first accessing the documentation, wait a moment for the server to fully start and refresh the page.

## Usage

Packflow provides a flexible base class called an `InferenceBackend` that allows users to build highly scalable platform- and tool-agnostic inference code, enabling simplified sharing across environments.

Additionally, Packflow's CLI can assist with creating projects, gathering environmental information, and creating distributable code packages for sharing reproducible inference code between disconnected environments.

For detailed information and usage patterns on Packflow, please see the `About Packflow` and `User Guide` sections of the official documentation site.

### Dummy Inference Backend

To create a dummy Inference Backend, update the `inference.py` file to the following:

```python
from packflow import InferenceBackend


class Backend(InferenceBackend):
    def execute(self, inputs):
        """
        Simply print 'Hello, world!' then return the input data
        """
        print('Hello, world!')
        return inputs
```

### Load and Run the Inference Backend

In a different Python file or from the command line in the same directory, execute the following:

```python
from packflow.loaders import LocalLoader

backend = LocalLoader('inference:Backend').load()

backend({"sample": "data"})
# >> {"sample": "data"}
```

## Contributing

Contributions to Packflow are welcomed and highly encouraged! Please refer to the [CONTRIBUTE.md](CONTRIBUTE.md) guide for more information and guidelines for contributing to Packflow.

## Authors

Packflow is developed and maintained by [Booz Allen Hamilton](https://www.boozallen.com/) on behalf of the Federal Government of the United States of America and the Department of War's Chief Digital and Artificial Intelligence Office (CDAO).

## License

`packflow` is distributed under the terms of the [MIT license](https://spdx.org/licenses/MIT.html). Please refer to the [LICENSE.txt](./LICENSE) for more information of acceptable usage and distribution of Packflow.


[^1]: *Pandoc* must be installed separately from the `pandoc` python package in `docs/requirements.txt`.
[^2]: Installation of `make` varies by operating system. On MacOS, install `xcode-select`. On Windows, it is recommend to use Windows Subsystem for Linux (WSL). On Debian/Ubuntu, `make` can be installed via `apt` package manager: <pre>
  sudo apt update
  sudo apt install make build-essential
</pre>
