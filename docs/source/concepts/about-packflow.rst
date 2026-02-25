.. _about-packflow:

About Packflow
==============

What is Packflow?
-----------------
``packflow`` is a software development kit (SDK) that simplifies the development process for writing production-ready
inference code and standardizes packaging of AI/ML running on streaming data sources.

Many existing packaging frameworks are catered towards inference APIs and often require custom preprocessing steps. This
can be particularly challenging when dealing with data sources that typically generate data one row at a time in key-value
pairs (e.g., firewall logs or message streams).

Packflow, however, is optimized to run models on batches of such events, streamlining development and reducing the need
for additional preprocessing. By leveraging Packflow, teams can focus on building and deploying models with custom
out-of the-box workflows and utilities, significantly reducing the time and effort required to onboard new
capabilities.

Packflow also ships with a lightweight command-line interface (CLI) that can scaffold new projects, template code, and archive or package
project files in a consistent, reproducible format, enabling customizable and maintainable deployment pipelines for
downstream users.

What is Packflow Not?
---------------------
Packflow is **not** meant to facilitate or replace any steps relating to model training or validation. A Packflow
project should contain only the required artifacts (e.g., serialized model files), requirements, and code for
**inference**. Including additional training artifacts and code may result in Packflow gathering incorrect runtime 
requirements or lead to unnecessary latency.

Terminology
-----------
The following terms are essential to understanding the ``packflow`` framework:

**Core Definitions**

* **Event**: A single, discrete unit of data processed by the model. It is analogous to a row in a dataset.
* **Batch**: A collection of events, represented as a list of length N, where each element is an individual event.
* **Records**: The data structure containing a batch of events, typically a list of dictionaries. This term is inspired by ``pandas`` and used extensively throughout the documentation.

.. Config used to be listed here; it has been temporarily disabled while we rework the
.. terminology between the Backend Configuration and the Packflow configuration.
.. The previous definition was:
.. * **Config**: Refers specifically to the configuration settings for a Model Backend. Configurations can be passed as keyword arguments in code or loaded from a ``config.json`` file.
