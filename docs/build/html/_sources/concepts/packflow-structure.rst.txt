Structure of a Packflow Project
===============================

Packflow provides utilities for ensuring projects are archived in a consistent, reproducible format, ensuring downstream
users can process and deploy Packflow projects in a reliable or automated fashion.

The ``packflow`` CLI provides a lightweight templating command, ``packflow create ...``, to initialize a Packflow project, consisting of the following files:


.. list-table::
   :width: 100%
   :widths: 10 10 40 40
   :header-rows: 1


   * - File
     - Required
     - Description
     - Default State
   * - ``packflow.yaml``
     - Yes
     - high-level metadata and configuration file housing information such as Python version, Inference Backend class, etc.
     - Template
   * - ``requirements.txt``
     - Yes
     - requirements file specifying the list of Python dependencies
     - Incomplete
   * - ``MODEL_CARD.md``
     - Recommended
     - markdown file documenting model details, limitations, ownership, etc.
     - Template
   * - ``LICENSE.txt``
     - Recommended
     - the applicable licensing information for the project
     - Blank
   * - ``README.md``
     - Recommended
     - readme file for use by developers and other contributors
     - Blank
   * - ``inference.py``
     - Yes
     - inference file containing the ``Backend`` execution object
     - Template
   * - ``validate.py``
     - Recommended
     - validation file which can be run to ensure the ``Backend`` adheres to ``InferenceBackend`` requirements
     - Template

The ``packflow`` CLI also contains the ``packflow export ...`` command for bundling these components into a single zipped archive,
simplifying the process of sharing and deploying inference code across different organizations and environments.

See the :ref:`CLI Reference<cli-reference>` for details on these commands.
