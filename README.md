<h1 align="center" style="text-align: center; border-bottom: none !important;">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/dow-cdao/packflow/master/assets/packflow-logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/dow-cdao/packflow/master/assets/packflow-logo-light.png">
    <img src="https://raw.githubusercontent.com/dow-cdao/packflow/master/assets/packflow-logo-dark.png" width="500" alt="Packflow logo">
  </picture>
</h1>

<p align="center">
  <a href="https://pypi.org/project/packflow/"><img alt="Packflow on PyPI - Version" src="https://img.shields.io/pypi/v/packflow">
</a>
  <a href="https://pypi.org/project/packflow/"><img alt="Packflow on PyPI - Python Versions" src="https://img.shields.io/pypi/pyversions/packflow">
</a>
<a href="https://github.com/dow-cdao/packflow/blob/master/LICENSE">
  <img alt="Packflow on GitHub - License" src="https://img.shields.io/github/license/dow-cdao/packflow">
</a>
</p>

# Introduction

`packflow` is a software development kit (SDK) that simplifies the development process and standardizes packaging of AI/ML
running on streaming data sources.

**What does Packflow do?** Packflow provides a framework for *writing*, *running*, and *packaging* inference code. It offers a standardized structure (the `InferenceBackend` class) for writing model execution logic, provides the runtime backbone that executes models with built-in profiling and preprocessing, and includes tools to bundle code into portable zip archives. This means you write your inference code once using Packflow's structure, and Packflow handles both the optimized execution and creation of shareable packages for transfer between systems.

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

> [!NOTE]
> If contributing to Packflow, it is recommended to install `packflow` from source in editable mode: `pip install -e .`

## Documentation

Packflow documentation is hosted at **[https://dow-cdao.github.io/packflow/](https://dow-cdao.github.io/packflow/)**. Pre-built HTML is also available on the [`gh-pages`](https://github.com/dow-cdao/packflow/tree/gh-pages) branch.

To build and serve documentation locally:

1. Install system prerequisites: [**Pandoc**](https://pandoc.org/installing.html) (required in addition to the `pandoc` Python package) and **`make`**[^2]
2. Navigate to the docs folder: `cd docs`
3. Install Python dependencies: `pip install -r requirements.txt`
4. Run `make dev` to serve with live reloading at [https://127.0.0.1:8000/](https://127.0.0.1:8000/)

## Usage

Packflow provides a flexible base class called an `InferenceBackend` that allows users to build highly scalable platform- and tool-agnostic inference code, enabling simplified sharing across environments.

Additionally, Packflow's CLI can assist with creating projects, gathering environmental information, and creating distributable code packages for sharing reproducible inference code between disconnected environments.

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

Contributions to Packflow are welcomed and highly encouraged! Please refer to the [CONTRIBUTING.md](https://github.com/dow-cdao/packflow/blob/master/CONTRIBUTING.md) guide for more information and guidelines for contributing to Packflow.

## Authors

Packflow is developed and maintained by [Booz Allen Hamilton](https://www.boozallen.com/) on behalf of the Federal Government of the United States of America and the Department of War's Chief Digital and Artificial Intelligence Office (CDAO).

## License

`packflow` is distributed under the terms of the [MIT license](https://spdx.org/licenses/MIT.html). Please refer to the [LICENSE](https://github.com/dow-cdao/packflow/blob/master/LICENSE) for more information of acceptable usage and distribution of Packflow.


[^2]: Installation of `make` varies by operating system. On MacOS, install `xcode-select`. On Windows, it is recommend to use Windows Subsystem for Linux (WSL). On Debian/Ubuntu, `make` can be installed via `apt` package manager: <pre>
  sudo apt update
  sudo apt install make build-essential
</pre>
