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

   # For contributors: install in editable mode
   pip install -e .


**Viewing Pre-built Documentation**

The simplest way to view the Packflow documentation is to serve the pre-build HTML files included in the repository:

.. code-block:: bash

   # Navigate to the pre-built docs folder
   cd docs/built/html

   # Start a local web server
   python -m http.server 8000

   # Access the documentation in a web browser at http://127.0.0.1:8000/


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

Initialize a new project by running ``packflow create hello-world``. This will create a new directory named ``hello-world`` that contains the following directory structure:
::

   hello-world/
   ├── packflow.yaml
   ├── LICENSE.txt
   ├── MODEL_CARD.md
   ├── README.md
   ├── requirements.txt
   ├── inference.py
   └── validate.py


Step 2: Write the Inference Backend
-----------------------------------

Open the ``inference.py`` with a code or text editor of your choice. Some templated code will be provided. Populate the ``execute()`` function with logic to double the value under the key ‘number’, and return the doubled number:

.. literalinclude:: code-examples/getting-started/inference.py
   :language: python
   :caption: inference.py
   :linenos:

The Inference Backend is now ready to be loaded, validated, and shared.


Step 3: Local Validation
------------------------

Now that the Inference Backend is written, use the built-in validation to ensure it will run as expected in production.

This can be done programmatically. Open the ``validate.py`` script and modify it to match the Inference Backend's inputs:

.. literalinclude:: code-examples/getting-started/validate.py
   :language: python
   :caption: validate.py
   :linenos:


.. note::

   Validation can be run via the ``validate.py`` file, or directly from a Notebook. However the path will ned to be updated
   if it is not running in the same directory

   Passing ``"inference:Backend"`` to the Local Loader is roughly equal to ``from inference import Backend``. If the script
   is nested further, the path can be separated via dot notation, such as ``src.mypackage.inference:Backend``.

If any validations fail, an exception message containing details of the issue and what needs to be fixed will be returned.

.. _getting_started_next_steps:

Next Steps
==========

Please see the :ref:`Creating a Custom Backend<custom-backends>` section of this site for more detailed information on building custom Inference Backends with Packflow.
