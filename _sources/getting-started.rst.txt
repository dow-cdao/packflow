.. _getting-started:

Getting Started
###############

This guide covers Packflow installation and basic usage of the CLI to create a simple Packflow project.


Installing Packflow
===================

**Prerequisites**

- **Python** (version 3.10+)


**Install from PyPI**

Packflow can be installed directly from PyPI:

.. code-block:: bash

   pip install packflow


**Install from Source**

For development or to install from source:

.. code-block:: bash

   # Clone repository and navigate to the root directory
   git clone https://github.com/dow-cdao/packflow.git
   cd packflow

   # Install package
   pip install .

   # For contributors: install in editable mode with dev dependencies
   pip install -e .[dev]

   # Alternative: use Poetry for dependency management
   poetry install --with dev

   # For contributors: install pre-commit hooks
   pre-commit install


**Documentation**

Packflow documentation is hosted at `https://dow-cdao.github.io/packflow/ <https://dow-cdao.github.io/packflow/>`_. For instructions on building documentation locally, see the `README <https://github.com/dow-cdao/packflow#documentation>`_.


.. important::
   If a "Not Found" error page is received when first accessing the documentation, wait a moment for the server to fully start and refresh the page.


**Building Documentation from Source**

The following are required to build documentation from source:

- **Python** (version 3.10+)
- **Pip**
- **Packflow** (the version corresponding to the docs being served)
- **Pandoc** - Must be installed separately, from system package manager (see `Pandoc installation instructions <http://pandoc.org/installing.html>`_)
- **make** command (``xcode-select`` on macOS and WSL on Windows, or ``build-essential`` on Linux)

Steps to build and serve documentation:

.. code-block:: bash

   # Navigate to docs folder
   cd docs

   # Install Python dependencies
   pip install -r requirements.txt

   # Serve documentation with live updates (development)
   make dev

   # OR serve static multi-version documentation (production)
   make prod-serve

   # Access the documentation in a web browser at http://127.0.0.1:8000/


Creating a Packflow Project
===========================

This section covers the initial setup process for creating a Packflow project, defining an Inference Backend, and running Packflow's validation checks on the input/output requirements of the Inference Backend.


Step 1: Create the project structure
------------------------------------

Initialize a new project by running ``packflow create hello-world``. An interactive wizard will prompt for a project description, version, and maintainer email. Defaults can be accepted by pressing Enter.

.. note::
   Project names must start with a letter and may contain letters, digits, hyphens, and underscores. To skip interactive prompts (e.g. in CI), pass ``--no-input``.

This creates a new directory named ``hello-world`` with the following structure:

::

   hello-world/
   ├── packflow.yaml
   ├── LICENSE.txt
   ├── MODEL_CARD.md
   ├── README.md
   ├── requirements.txt
   ├── inference.py
   └── tests.py


Step 2: Write the Inference Backend
-----------------------------------

Open ``inference.py``. The template contains a passthrough backend that returns inputs unchanged. Replace the ``execute()`` method with logic for the analytic. For this example, the backend doubles the value under the key ``number``:

.. literalinclude:: code-examples/getting-started/inference.py
   :language: python
   :caption: inference.py
   :linenos:


Step 3: Test the Backend (Optional)
------------------------------------

A ``tests.py`` file is included as a starting point for testing the backend with ``pytest``. This file is optional and not required for validation or export. To use it, update the sample inputs to match the backend’s expected format:

.. literalinclude:: code-examples/getting-started/tests.py
   :language: python
   :caption: tests.py
   :linenos:

Run the tests from inside the project directory:

.. code-block:: bash

   pip install pytest
   pytest tests.py

The ``test_check_io`` test calls ``backend.check_io()``, which runs sample data through the backend and checks that outputs meet Packflow’s format requirements (correct types, matching row counts, JSON-serializable values). If any checks fail, an exception with details of the issue is raised.


Step 4: Validate the project
-----------------------------

Use the ``packflow validate`` command to check that the project structure and configuration are complete:

.. code-block:: bash

   packflow validate

This checks for required files (``packflow.yaml``, ``requirements.txt``), recommended files (``README.md``, ``MODEL_CARD.md``, ``LICENSE.txt``), metadata completeness, and runs a smoke test to verify the backend can be loaded.

Pass ``-v`` for detailed output showing each check.


Step 5: Package for distribution
--------------------------------

Once the backend is implemented, tested, and validated, create a distributable archive:

.. code-block:: bash

   packflow export

This produces a zip file (e.g. ``hello_world-0.1.0.zip``) in the current directory. See :ref:`Preparing for Distribution<distribution>` for details on what is included in the archive and how to prepare a project for sharing.

.. _getting_started_next_steps:

Next Steps
==========

Please see the :ref:`Creating a Custom Backend<custom-backends>` section of this site for more detailed information on building custom Inference Backends with Packflow.
