.. _distribution:

Preparing for Distribution
##########################

This documentation describes how to create a distributable version of the model backend for sharing inference code.

Before Distribution
===================

The Inference Backend should be :ref:`validated <validation>` and :ref:`tested<best-practices-testing>` before distribution. The following files should also be completed before packaging:

 - ``MODEL_CARD.md``: Document model details, limitations, and ownership.
 - ``README.md``: Provide usage instructions and relevant information for developers and contributors.
 - ``LICENSE.txt``: Specify the applicable licensing information for the project.
 - ``packflow.yaml``: Complete all metadata and configuration fields.
 - ``requirements.txt``: Specify all required Python dependencies.

These files are created as part of the Packflow project structure when initializing a new project with the ``packflow create`` command.

Packflow Config File
====================
After initializing a project with the ``packflow create`` command, a file named ``packflow.yaml`` will be automatically
generated in the project structure. This file contains information that Packflow can read to load the
project, and presents a natural integration surface for other systems to load and interact with Packflow-built analytics.

Contents
--------

The purpose of ``packflow.yaml`` is to track:

1. Project metadata, including ``name``, ``version``, ``description``, and ``maintainers``.  
    - This information could be used as a part of a DevOps pipeline or workflow designed to efficiently import Packflow projects into a system. 

.. note::
     For instance, a DevOps pipeline could send automated emails to warn the maintainers of an issue with running the project, or to alert them of a vulnerability detected in one of the project's dependencies.

2. Loader configuration, including ``python_version``, ``inference_backend``, and ``loader``.
    - These configuration fields specify how an Inference Backend may be loaded from the Packflow project.

3. Custom configuration/metadata fields
    - If there are any other project-scope configurations or metadata that needs to be tracked, arbitrary configuration values are accepted here.

.. note:: 
    Please also consider :ref:`Backend Configuration<backend-configuration>` for configurations specific to Packflow's preprocessors or Inference Backend, and for defining :ref:`custom configurations<custom-config-models>` and behaviors in the ``InferenceBackend`` controlled by the backend config.

Creating a Package
==================

Create a distributable package using the ``packflow export [PROJECT_PATH]`` command.

.. code-block:: bash

    packflow export [PROJECT_PATH]

The ``[PROJECT_PATH]`` argument is optional; if not provided, the current working directory will be used as the project path.

This will create a zipped archive of the Packflow project in the current working directory, which can then be shared and deployed across different environments.

.. note::
    In the archive filename, hyphens in the project name are replaced with underscores (e.g., ``my-analytic`` produces ``my_analytic-1.0.0.zip``).
    This follows `PEP 625 <https://peps.python.org/pep-0625/>`_ conventions, ensuring the hyphen in the filename unambiguously separates the project name from the version.

.. note::
    Each package corresponds to a release. Creating packages from Git branches or tags is recommended for versioning.
